from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os
import json
import networkx as nx
from typing import List, Dict
import re

from .models import Paper

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_initial_categories(sample_papers: List[Paper]) -> List[str]:
    
    """
    ・Generate broad initial categories for the research papers based on their titles and abstracts.
    ・The prompt guides the LLM to create categories that are general enough to cover multiple papers 
    ・but specific enough to be meaningful. These categories serve as a starting point for further refinement.
    """
    
    papers_data = [{"title": p.title, "abstract": p.abstract} for p in sample_papers] 

    prompt = f"""
    Generate research categories that best represent the content of the following papers. 
    Provide the categories as a numbered list, with each category on a new line.
    
    Each category should:
    1. Be between 4-8 words long
    2. Represent a broad research area or methodology
    3. Be general enough to encompass multiple related papers
    4. Reflect both methodologies and research goals
    5. Avoid overly technical jargon unless necessary
    6. Use terminology that reflects common research areas recognized in the field

    Aim for 7-10 categories that cover the major themes in the papers.
    Ensure that the categories are distinct and mutually exclusive where possible.
    Ensure that each category is complete and does not get cut off midway.

    Papers:
    {json.dumps(papers_data, indent=2)}

    Categories:
    """

    response = client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": "You are an expert in categorizing scientific research papers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,  
        max_tokens=1000
    )

    raw_output = response.choices[0].message.content.strip()
    
    categories = raw_output.split("\n")
    categories = [re.sub(r'^\d+\.\s*', '', cat.strip()) for cat in categories]

    # Ensure that each category is complete and does not get cut off midway.
    return [cat for cat in categories if cat]

# Function to refine generated categories based on feedback and further analysis
def refine_categories(categories: List[str], sample_papers: List[Paper]) -> List[str]:

    """
    ・Refine the initial categories to better align with recognized research areas.
    ・This process involves merging similar categories and splitting broad ones to ensure clarity and specificity.
    ・The goal is to create categories that are distinct, meaningful, and reflective of the research field's structure.
    """
      
    sample_papers_data = [{"title": p.title, "abstract": p.abstract} for p in sample_papers]

    prompt = f"""
    Based on the initial categories and the sample papers provided, refine and improve the categories to better align with recognized research areas.

    Your task:
    1. Merge categories that are too similar or overlapping
    2. Split categories that are too broad into more specific subfields
    3. Ensure each category clearly differentiates from others and reflects a specific research theme
    4. Use terminology that is widely recognized in academic and professional research
    5. Maintain a balance between broad categories and specific subfields

    Aim to produce 7-10 refined categories.
    Ensure that each category is complete and does not get cut off midway.

    Initial Categories:
    {json.dumps(categories, indent=2)}

    Sample Papers:
    {json.dumps(sample_papers_data, indent=2)}

    Provide your refined categories as a numbered list, with each category on a new line. 

    Refined Categories:
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert in refining research categories."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1000
    )

    raw_output = response.choices[0].message.content.strip()

    refined_categories = raw_output.strip().split('\n')
    refined_categories = [re.sub(r'^\d+\.\s*', '', cat.strip()) for cat in refined_categories]
    
    # Return the first 50 characters of each category(discard the rest)
    # return [cat[:50] for cat in refined_categories if cat]
    return [cat for cat in categories if cat]

def get_text_embedding(text: str, model: str = "text-embedding-3-large") -> np.array:
    
    """
    ・Generate a text embedding for the given input using the specified model.
    ・This is used to numerically represent the content of the text, enabling similarity calculations.
    """

    response = client.embeddings.create(input=[text], model=model)
    embedding = response.data[0].embedding
    return np.array(embedding)

def calculate_text_similarity(embedding1: np.array, embedding2: np.array) -> float:
    
    dot_product = np.dot(embedding1, embedding2)
    
    norm1 = np.linalg.norm(embedding1)
    norm2 = np.linalg.norm(embedding2)
    
    similarity = dot_product / (norm1 * norm2)
    
    return similarity

def compute_category_similarity_matrix(category_names: List[str]) -> Dict[tuple[str, str], float]:
    
    """
    ・Compute pairwise similarities between all categories based on their text embeddings.
    ・This helps to understand the relationships and potential overlaps between categories, 
    ・which is useful for further refinement and ordering of categories.
    """
    
    category_embedding_dict = {
        category: get_text_embedding(category) 
        for category in category_names
    }
    # {"Machine Learning": np.array([0.2, 0.4, ...]), "Data Science": np.array([0.1, 0.3, ...]), "Robotics": np.array([0.5, 0.7, ...])}
    
    # Compute pairwise similarities
    similarity_matrix = {}
    for i, cat1 in enumerate(category_names):
        for cat2 in category_names[i+1:]:
            similarity = calculate_text_similarity(
                category_embedding_dict[cat1],
                category_embedding_dict[cat2]
            )
            similarity_matrix[(cat1, cat2)] = similarity
    
    return similarity_matrix
    #relations = {
    #("Lab Automation", "DNA Sequencing"): 0.75,
    #("Lab Automation", "Robotics"): 0.85,
    #("DNA Sequencing", "Robotics"): 0.60
    #}

def order_categories(category_names: List[str]) -> List[str]:
    # Compute similarities between categories
    category_similarities = compute_category_similarity_matrix(category_names)
    
    G = nx.Graph()
    G.add_weighted_edges_from([
        (cat1, cat2, 1 - weight)  
        for (cat1, cat2), weight in category_similarities.items()
    ])
    
    mst = nx.maximum_spanning_tree(G)
    
    start_node = max(mst.degree, key=lambda x: x[1])[0]
    
    # Perform a breadth-first search to order the categories
    ordered_categories = list(nx.bfs_tree(mst, start_node))
    
    # Add any categories that weren't included in the MST
    ordered_categories.extend([cat for cat in category_names if cat not in ordered_categories])
    
    return ordered_categories

def find_best_category_for_paper(paper: Paper, category_vector_dict: Dict[str, np.array]) -> str:

    """
    ・Identify the best matching category for a given paper by comparing its embedding to the category embeddings.
    ・This ensures that each paper is placed in the category that is most semantically similar to its content.
    """

    # Initialize an empty string to hold the concatenated title and abstract
    paper_content = ""
    if paper.title is not None:
        paper_content += paper.title + " "
    if paper.abstract is not None:
        paper_content += paper.abstract
    
    # Generate an embedding for the paper based on the concatenated title and abstract
    paper_vector = get_text_embedding(paper_content)
    
    # Calculate similarities between paper and each category
    # { "Machine Learning Algorithms": 0.92, "Data Preprocessing Techniques": 0.68, ... }
    category_similarity_dict = {
        category_name: calculate_text_similarity(paper_vector, category_vector)
        for category_name, category_vector in category_vector_dict.items()
    }
    
    best_matching_category = max(category_similarity_dict, key=category_similarity_dict.get)
    return best_matching_category

def classify_papers_into_categories(papers: List[Paper], category_names: List[str]) -> Dict[str, List[Paper]]:
    
    """
    ・Classify each paper into the most appropriate category based on embedding similarity.
    ・The goal is to ensure that each category contains papers that are closely related in content.
    """
    
    # Generate embeddings for all categories
    category_embedding_dict = {
        category: get_text_embedding(category) 
        for category in category_names
    }
    
    # Initialize the classification dictionary
    classification_result = {category: [] for category in category_names}
    
    # Classify each paper
    for paper in papers:
        best_category = find_best_category_for_paper(paper, category_embedding_dict)
        classification_result[best_category].append(paper)
    
    # Remove any empty categories
    classification_result = {
        category: paper_list 
        for category, paper_list in classification_result.items() 
        if paper_list
    }
    
    return classification_result

def generate_headings(papers: list[Paper]) -> dict[str, list[Paper]]:
    try:

        # sample_papers_for_initial = systematic_sampling(papers, 3)
        initial_categories = generate_initial_categories(papers)
        # sample_papers_for_refined = systematic_sampling(papers, 4)
        refined_categories = refine_categories(initial_categories, papers)

        ordered_categories = order_categories(refined_categories)

        classifications = classify_papers_into_categories(papers, ordered_categories)

        # Remove empty categories
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
    # {'Goal-directed Robotic Scripting in Biolo': 
    #   [Paper(id='5ec18c8777e0eaf1411987638040546a22da861e', 
    #   title='LLMs can generate robotic scripts from goal-oriented instructions in biological laboratory automation', 
    #   abstract="The use of laboratory automation by all researchers may substantially accelerate scientific activities by humans, including those in the life sciences. However, computer programs to operate robots should be written to implement laboratory automation, which requires technical knowledge and skills that may not be part of a researcher's training or expertise. In the last few years, there has been remarkable development in large language models (LLMs) such as GPT-4, which can generate computer codes based on natural language instructions. In this study, we used LLMs, including GPT-4, to generate scripts for robot operations in biological experiments based on ambiguous instructions. GPT-4 successfully generates scripts for OT-2, an automated liquid-handling robot, from simple instructions in natural language without specifying the robotic actions. Conventionally, translating the nuances of biological experiments into low-level robot actions requires researchers to understand both biology and robotics, imagine robot actions, and write robotic scripts. Our results showed that GPT-4 can connect the context of biological experiments with robot operation through simple prompts with expert-level contextual understanding and inherent knowledge. Replacing robot script programming, which is a tedious task for biological researchers, with natural-language LLM instructions that do not consider robot behavior significantly increases the number of researchers who can benefit from automating biological experiments.", venue='', year=2023, authors=[Author(id='2054037213', name='T. Inagaki'), Author(id='2214922490', name='Akari Kato'), Author(id='2116095075', name='Koichi Takahashi'), Author(id='50075919', name='Haruka Ozaki'), Author(id='35226027', name='G. Kanda')])], 'NGS Library Prep Automation Challenges &': [Paper(id='85b19a6f5597689fe4dedb3954aff3026e75ea20', title='Implementing laboratory automation for...
    # }
if __name__ == "__main__":
    # Assume 'papers' is a list of dictionaries, each containing 'title' and 'abstract' keys
    generate_headings([])