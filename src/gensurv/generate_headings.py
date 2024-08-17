import gensim
from gensim import corpora
from transformers import pipeline
from openai import OpenAI
import numpy as np
from papers_data import papers
from dotenv import load_dotenv
import os
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_initial_categories(papers: List[Dict[str, str]], num_categories: int = 10) -> List[str]:
    prompt = f"""
    Given the following list of paper titles and abstracts, generate {num_categories} research categories that best represent the content. 
    Provide the categories as a comma-separated list. 
    Each category should:
    1. Be 20-30 characters long
    2. Provide meaningful insights into the specific research area
    3. Be sufficiently specific to distinguish between different subfields
    4. Reflect the methodologies, technologies, or key concepts discussed in the papers
    5. Avoid overly general terms like "Artificial Intelligence" or "Machine Learning"
    6. Use technical terminology appropriate for the field

    Consider the following examples of good categories:
    - "Metabolic network modeling"
    - "Genome-scale flux analysis"
    - "Synthetic biology automation"
    - "Multi-omics data integration"

    Papers:
    {json.dumps([{"title": p["title"], "abstract": p["abstract"][:100] + "..."} for p in papers[:20]], indent=2)}

    Categories:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates research categories based on academic papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    raw_output = response.choices[0].message.content.strip()
    categories = [re.sub(r'^["\'\s]+|["\'\s]+$', '', cat.strip()) for cat in raw_output.split(",")]
    return [cat[:30] for cat in categories]  # Ensure categories are no longer than 30 characters

def refine_categories(categories: List[str], papers: List[Dict[str, str]]) -> List[str]:
    prompt = f"""
    Given the following initial categories and a sample of papers, refine and adjust the categories to better represent the research areas. 
    You can modify, combine, split, or create new categories as needed. Aim for clarity, distinctiveness, and specificity.
    Each category should:
    1. Be 20-30 characters long
    2. Provide meaningful insights into the specific research area
    3. Be sufficiently specific to distinguish between different subfields
    4. Reflect the methodologies, technologies, or key concepts discussed in the papers
    5. Avoid overly general terms
    6. Use technical terminology appropriate for the field
    7. Ensure minimal overlap between categories

Provide the refined categories as a comma-separated list.

    Initial Categories:
    {json.dumps(categories, indent=2)}

    Sample Papers:
    {json.dumps([{"title": p["title"], "abstract": p["abstract"][:100] + "..."} for p in papers[:10]], indent=2)}

    Refined Categories:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that refines research categories based on academic papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    raw_output = response.choices[0].message.content.strip()
    refined_categories = [re.sub(r'^["\'\s]+|["\'\s]+$', '', cat.strip()) for cat in raw_output.split(",")]
    return [cat[:30] for cat in refined_categories if cat]  # Ensure categories are no longer than 30 characters and not empty

def classify_paper(paper: Dict[str, str], categories: List[str]) -> str:
    prompt = f"""
    Classify the following paper into the most appropriate category from the list provided. 
    If none of the categories fit well, respond with "Other".

    Categories:
    {json.dumps(categories, indent=2)}

    Paper:
    Title: {paper["title"]}
    Abstract: {paper["abstract"]}

    Category:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies academic papers into research categories."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error classifying paper: {e}")
        return "Error"

def classify_papers_batch(papers: List[Dict[str, str]], categories: List[str], batch_size: int = 10) -> Dict[str, List[str]]:
    classifications = {cat: [] for cat in categories + ["Other", "Error"]}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i+batch_size]
            futures = [executor.submit(classify_paper, paper, categories) for paper in batch]
            for future, paper in zip(as_completed(futures), batch):
                category = future.result()
                if category not in classifications:
                    classifications["Error"].append(paper["title"])
                else:
                    classifications[category].append(paper["title"])
    
    return classifications

def analyze_results(classifications: Dict[str, List[str]], papers: List[Dict[str, str]]) -> str:
    num_papers = len(papers)
    num_categories = len(classifications)
    avg_papers_per_category = num_papers / num_categories

    prompt = f"""
    Analyze the following classification results and suggest improvements:

    Total papers: {num_papers}
    Number of categories: {num_categories}
    Average papers per category: {avg_papers_per_category:.2f}

    Classification distribution:
    {json.dumps({cat: len(titles) for cat, titles in classifications.items()}, indent=2)}

    Suggestions for improvement:
    1. Propose any categories that should be split or combined.
    2. Identify any categories that are too broad or too narrow.
    3. Suggest new categories that might better represent the research areas.
    4. Comment on the overall distribution of papers across categories.

    Provide your analysis and suggestions:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes research paper classifications and suggests improvements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error analyzing results: {e}"

def main(papers: List[Dict[str, str]]):
    try:
        # Step 1: Generate initial categories
        initial_categories = generate_initial_categories(papers)
        print("Initial Categories:", initial_categories)

        # Step 2: Refine categories
        refined_categories = refine_categories(initial_categories, papers)
        print("Refined Categories:", refined_categories)

        if not refined_categories:
            print("Error: No refined categories generated. Using initial categories.")
            refined_categories = initial_categories

        # Step 3: Classify papers in batches
        classifications = classify_papers_batch(papers, refined_categories)

        # Step 4: Output results
        print("\nClassification Results:")
        for category, titles in classifications.items():
            print(f"\n{category}:")
            for title in titles:
                print(f"- {title}")

        # Step 5: Analyze results and suggest further refinements
        analysis = analyze_results(classifications, papers)
        print("\nAnalysis and Suggestions:")
        print(analysis)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Assume 'papers' is a list of dictionaries, each containing 'title' and 'abstract' keys
    main(papers)

# from openai import OpenAI
# import json
# from dotenv import load_dotenv
# import os

# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def classify_paper(title, headings):
#     prompt = f"""
#     Task: Classify the given paper title into the most appropriate heading.

#     Headings:
#     {json.dumps(headings)}

#     Paper Title: "{title}"

#     Classify the paper title into the most appropriate heading. Respond with only the heading name.
#     """

#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant that classifies academic paper titles into appropriate headings."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.3,
#         max_tokens=50
#     )

#     return response.choices[0].message.content.strip()

# def main():
#     headings = ["AI and Machine Learning", "Natural Language Processing", "Computer Vision"]
#     paper_titles = [
#         "Attention Is All You Need",
#         "Deep Residual Learning for Image Recognition",
#         "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"
#     ]

#     classification_results = {}
#     for title in paper_titles:
#         classified_heading = classify_paper(title, headings)
#         classification_results[title] = classified_heading

#     print("Classification Results:")
#     print(json.dumps(classification_results, indent=2))

#     grouped_results = {}
#     for title, heading in classification_results.items():
#         if heading not in grouped_results:
#             grouped_results[heading] = []
#         grouped_results[heading].append(title)

#     print("\nGrouped Results:")
#     print(json.dumps(grouped_results, indent=2))

# if __name__ == "__main__":
#     main()