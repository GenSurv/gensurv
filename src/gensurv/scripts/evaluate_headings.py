# This script evaluates the quality of generated categories (headings) by comparing them with evaluation categories. 
# This script's results provide insights into how to improve generate_headings.py to better categorize research papers.

import argparse
import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import os
from openai import OpenAI

from ..generate_headings import generate_headings
from ..models import Paper

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def parse_args():
    parser = argparse.ArgumentParser()
    # if you want to try dataset from filemaker, need to implement create_dataset.py first
    parser.add_argument("--input_data_path", type=Path, required=True)
    parser.add_argument("--eval_data_path", type=Path, required=True)
    return parser.parse_args()

def load_papers(papers_path: Path) -> List[Paper]:
    with open(papers_path, "r") as f:
        data = json.load(f)
    #    [
    #     {
    #         "id": "1",
    #         "title": "Single-cell microbiology: tools, technologies, and applications",
    #         "abstract": "The field of microbiology has traditionally been concerned with and focused on studies at the population level...",
    #         "venue": "",
    #         "year": "",
    #         "authors": [
    #             {"id": "", "name": ""}
    #         ]
    #     },
    #    ]
    
    processed_data = []
    for paper_data in data:

        if paper_data.get("year") == "":
            paper_data["year"] = None
        
        if "citation_styles" not in paper_data:
            paper_data["citation_styles"] = None
        
        processed_data.append(Paper(**paper_data))
    
    return processed_data
    # [
    #     Paper(
    #         id="1",
    #         title="Single-cell microbiology: tools, technologies, and applications",
    #         abstract="The field of microbiology has traditionally been concerned with and focused on studies at the population level...",
    #         venue="",
    #         year=None,  # Converted from an empty string to None
    #         authors=[Author(id="", name="")]
    #     ),
    # ]

def load_eval_headings(eval_headings_path: Path) -> List[Dict[str, List[str]]]:
    with open(eval_headings_path, "r") as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "headings" in data:
        return data["headings"]
    # [
    #     {
    #         "heading": "Single-cell isolation techniques",
    #         "papers": [...]
    #     },
    #     {
    #         "heading": "Comparative analysis for scRNA-seq library preparation",
    #         "papers": [...]
    #     }
    # ]
    else:
        raise ValueError("The structure of eval_headings file is incorrect.")

def evaluate_headings(generated_headings: Dict[str, List[Paper]], eval_headings: List[Dict[str, List[str]]]) -> Dict[str, float]:
    evaluation_results = []

    for gen_heading, gen_papers in generated_headings.items():
        gen_titles = {paper.title for paper in gen_papers}
        
        # The goal is to match generated categories to evaluation categories based on the overlap of paper titles.
        # This is done to assess how well the generated headings group similar papers together compared to a human-evaluated set.
        best_match = None
        best_match_score = 0
        for eval_heading in eval_headings:
            eval_titles = set(eval_heading["papers"])
            overlap_count = len(gen_titles.intersection(eval_titles))
            match_score = overlap_count / len(gen_titles.union(eval_titles))  # Jaccard similarity

            # We select the evaluation heading with the highest overlap as the best match for each generated heading.
            # This method ensures that the evaluation is based on the actual content (paper titles) rather than just the heading names.
            if match_score > best_match_score:
                best_match = eval_heading["heading"]
                best_match_score = match_score

        evaluation_results.append({
            "generated_heading": gen_heading,
            "best_matching_eval_heading": best_match,
            "matching_score": best_match_score,
            "generated_titles": sorted(gen_titles),
            "eval_titles": sorted(eval_titles),
        })

     # Display results to provide a clear comparison between generated and evaluated headings.
    print("\n===== Evaluation Results =====\n")
    for result in evaluation_results:
        print(f"### Generated Heading: {result['generated_heading']}")
        print(f"### Best Matching Evaluated Heading: {result['best_matching_eval_heading']}")
        print(f"### Matching Score: {result['matching_score']:.2f}\n")

        print("---- Papers under Generated Heading ----")
        for title in result["generated_titles"]:
            print(f"  - {title}")
        
        print("\n---- Papers under Best Matching Evaluated Heading ----")
        for title in result["eval_titles"]:
            print(f"  - {title}")

        print("\n" + "="*50 + "\n")

    # Returning the average matching score provides a quantitative measure of how well the generated headings align with the evaluation set.
    avg_matching_score = np.mean([result['matching_score'] for result in evaluation_results])
    return {
        "average_matching_score": avg_matching_score,
        "evaluation_details": evaluation_results
    }

def compare_paper_counts(generated_headings: Dict[str, List[Paper]], eval_headings: List[Dict[str, List[str]]]):
    
    generated_total_papers = sum(len(papers) for papers in generated_headings.values())
    eval_total_papers = sum(len(heading["papers"]) for heading in eval_headings)
    
    print(f"Total papers in generated headings: {generated_total_papers}")
    print(f"Total papers in evaluated headings: {eval_total_papers}")
    
    # The purpose of this check is to ensure that the total number of papers categorized is consistent between generated and evaluated headings.
    if generated_total_papers == eval_total_papers:
        print("The number of papers matches between generated and evaluated headings.")
    else:
        print("Mismatch detected in the number of papers between generated and evaluated headings.")

def main():
    args = parse_args()
    
    print("loading papers...")
    papers = load_papers(args.papers_path)
    eval_headings = load_eval_headings(args.eval_headings_path)

    print("Generating headings...")
    structured_papers = generate_headings(papers)
    # {
    #     "Single-cell isolation techniques": [
    #         Paper(
    #             id="1",
    #             title="Single-cell microbiology: tools, technologies, and applications",
    #             abstract="The field of microbiology has traditionally been concerned with and focused on studies at the population level...",
    #             venue="",
    #             year=None,
    #             authors=[Author(id="", name="")]
    #         ),
    #         Paper(
    #             id="2",
    #             title="Single-cell multi-omics sequencing of mouse early embryos and embryonic stem cells",
    #             abstract="Single-cell epigenome sequencing techniques have recently been developed...",
    #             venue="",
    #             year=None,
    #             authors=[Author(id="", name="")]
    #         )
    #     ],
    #     "Comparative analysis for scRNA-seq library preparation": [
    #         # Other papers would be classified here
    #     ]
    # }

    # generated_headings = list(structured_papers.keys())
    # # generated_headings = [
    # # "Single-cell isolation techniques",
    # # "Comparative analysis for scRNA-seq library preparation"
    # # ]

    print("Evaluating headings...")
    evaluate_headings(structured_papers, eval_headings)
    compare_paper_counts(structured_papers, eval_headings)

if __name__ == "__main__":
    main()