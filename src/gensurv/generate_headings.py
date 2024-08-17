from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from dataclasses import dataclass, field

from .models import Paper

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@dataclass
class Author:
    id: str
    name: str

@dataclass
class Paper:
    id: str
    title: str
    abstract: str
    venue: Optional[str] = None
    year: Optional[int] = None
    authors: List[Author] = field(default_factory=list)


def generate_initial_categories(papers: List[Paper], num_categories: int = 10) -> List[str]:

    # print("\nSTART: Generating Initial Categories")
    # print("======================================")

    # print("Input Data Check:")
    # for i, paper in enumerate(papers[:5], 1):  
    #     print(f"Paper {i}:")
    #     print(f"  Title: {paper.title}")
    #     print(f"  Abstract: {paper.abstract[:100]}...")  
    # print(f"Total number of papers: {len(papers)}")
    # print("\n")

    # papers_data = [{"title": p.title, "abstract": p.abstract[:100] + "..."} for p in papers[:20]]
    papers_data = [{"title": p.title, "abstract": p.abstract} for p in papers[:20]]

    prompt = f"""
    Generate exactly {num_categories} research categories that best represent the content of the following papers. 
    Provide the categories as a numbered list, with each category on a new line.
    
    Each category should:
    1. Be between 20 and 40 characters long
    2. End with a complete word or concept, not mid-word
    3. Use abbreviations if necessary to fit within 40 characters
    4. Provide meaningful insights into the specific research area
    5. Be sufficiently specific to distinguish between different subfields
    6. Reflect the methodologies, technologies, or key concepts discussed in the papers
    7. Avoid overly general terms like "Artificial Intelligence" or "Machine Learning"
    8. Use technical terminology appropriate for the field

    Consider the following examples of good categories:
    - "Metabolic network modeling"
    - "Genome-scale flux analysis"
    - "Synthetic biology automation"
    - "Multi-omics data integration"

    Papers:
    {json.dumps(papers_data, indent=2)}

    Categories:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates research categories based on academic papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )

    raw_output = response.choices[0].message.content.strip()
    # print("\nRaw Output:")
    # print("-----------")
    # print(raw_output)
    
    categories = raw_output.split("\n")
    categories = [re.sub(r'^\d+\.\s*', '', cat.strip()) for cat in categories]

    # print("\nEND: Generating Initial Categories")
    # print("====================================")
    return [cat[:40] for cat in categories] 


def refine_categories(categories: List[str], papers: List[Paper]) -> List[str]:

    # print("\nSTART: Refining Categories")
    # print("===========================")

    sample_papers_data = [{"title": p.title, "abstract": p.abstract} for p in papers[:20]]

    prompt = f"""
    Given the following initial categories and a sample of papers, significantly refine and improve the categories to better represent the research areas. 
    You MUST make substantial changes to the categories. Simply repeating the initial categories is not acceptable.

    Your task:
    1. Critically evaluate each initial category.
    2. Combine overlapping categories.
    3. Split broad categories into more specific ones.
    4. Create entirely new categories if needed.
    5. Ensure each category is distinct and non-overlapping.
    6. Aim to generate exactly {len(categories)} refined categories.

    Each refined category should:
    1. Be between 20 and 40 characters long
    2. End with a complete word or concept, not mid-word
    3. Use abbreviations if necessary to fit within 40 characters
    4. Provide deeper insights into the specific research area
    5. Be more specific and distinctive than the initial categories
    6. Reflect advanced methodologies, technologies, or key concepts
    7. Use precise technical terminology appropriate for experts in the field

    Important: Ensure that each category is a complete phrase or term, even if it means using fewer than 40 characters.

    Initial Categories:
    {json.dumps(categories, indent=2)}

    Sample Papers:
    {json.dumps(sample_papers_data, indent=2)}

    Provide your refined categories as a numbered list, with each category on a new line. 
    Ensure that your refined categories are substantially different from the initial ones.

    Refined Categories:
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that refines research categories based on academic papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=400
    )

    raw_output = response.choices[0].message.content.strip()
    # print("\nRaw Output:")
    # print("-----------")
    # print(raw_output)

    refined_categories = raw_output.strip().split('\n')
    refined_categories = [re.sub(r'^\d+\.\s*', '', cat.strip()) for cat in refined_categories]
    
    # print("\nCategory Comparison:")
    # print("--------------------")
    # for i, (initial, refined) in enumerate(zip(categories, refined_categories), 1):
    #     print(f"{i:2d}. Initial: {initial}")
    #     print(f"    Refined: {refined}")
    #     print()

    # print("\nEND: Refining Categories")
    # print("=========================")
    
    return [cat[:40] for cat in refined_categories if cat] 

def get_embedding(text: str, model: str = "text-embedding-3-small") -> np.array:
    response = client.embeddings.create(input=[text], model=model)
    embedding = response.data[0].embedding
    return np.array(embedding)

def cosine_similarity(embedding1: np.array, embedding2: np.array) -> float:
    return np.dot(embedding1, embedding2)

def classify_paper_by_similarity(paper: Paper, category_embeddings: Dict[str, np.array]) -> str:
    paper_embedding = get_embedding(paper.title + " " + paper.abstract)
    
    max_similarity = -1
    best_category = "Error"
    
    for category, embedding in category_embeddings.items():
        similarity = cosine_similarity(paper_embedding, embedding)
        if similarity > max_similarity:
            max_similarity = similarity
            best_category = category
    
    if max_similarity < 0.3:
        return "Error"
    
    return best_category

def classify_papers_batch(papers: List[Paper], categories: List[str]) -> Dict[str, List[Paper]]:
    category_embeddings = {category: get_embedding(category) for category in categories}
    classifications = {cat: [] for cat in categories}
    classifications["Error"] = []
    
    for paper in papers:
        category = classify_paper_by_similarity(paper, category_embeddings)
        classifications[category].append(paper)
    
    return classifications

def generate_headings(papers: list[Paper]) -> dict[str, list[Paper]]:
    try:
        initial_categories = generate_initial_categories(papers)
        refined_categories = refine_categories(initial_categories, papers) or initial_categories
        refined_categories = [cat[:40] for cat in refined_categories]
        classifications = classify_papers_batch(papers, refined_categories)
        # Classification Results: {'Goal-directed Robotic Scripting in Biolo': [Paper(id='5ec18c8777e0eaf1411987638040546a22da861e', title='LLMs can generate robotic scripts from goal-oriented instructions in biological laboratory automation', abstract="The use of laboratory automation by all researchers may substantially accelerate scientific activities by humans, including those in the life sciences. However, computer programs to operate robots should be written to implement laboratory automation, which requires technical knowledge and skills that may not be part of a researcher's training or expertise. In the last few years, there has been remarkable development in large language models (LLMs) such as GPT-4, which can generate computer codes based on natural language instructions. In this study, we used LLMs, including GPT-4, to generate scripts for robot operations in biological experiments based on ambiguous instructions. GPT-4 successfully generates scripts for OT-2, an automated liquid-handling robot, from simple instructions in natural language without specifying the robotic actions. Conventionally, translating the nuances of biological experiments into low-level robot actions requires researchers to understand both biology and robotics, imagine robot actions, and write robotic scripts. Our results showed that GPT-4 can connect the context of biological experiments with robot operation through simple prompts with expert-level contextual understanding and inherent knowledge. Replacing robot script programming, which is a tedious task for biological researchers, with natural-language LLM instructions that do not consider robot behavior significantly increases the number of researchers who can benefit from automating biological experiments.", venue='', year=2023, authors=[Author(id='2054037213', name='T. Inagaki'), Author(id='2214922490', name='Akari Kato'), Author(id='2116095075', name='Koichi Takahashi'), Author(id='50075919', name='Haruka Ozaki'), Author(id='35226027', name='G. Kanda')])], 'NGS Library Prep Automation Challenges &': [Paper(id='85b19a6f5597689fe4dedb3954aff3026e75ea20', title='Implementing laboratory automation for...

        non_empty_classifications = {cat: papers for cat, papers in classifications.items() if papers}

        print("\nClassification Results:\n")
        for category, classified_papers in non_empty_classifications.items():
            print(f"Category: {category} (Total: {len(classified_papers)})")
            for paper in classified_papers:
                print(f"  - {paper.title}")
            print("\n" + "="*40 + "\n")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
    return non_empty_classifications

if __name__ == "__main__":
    # Assume 'papers' is a list of dictionaries, each containing 'title' and 'abstract' keys
    generate_headings([])
