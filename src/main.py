from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

from gensurv import (
    generate_query, retrieve_papers, generate_headings, classify_papers, generate_overview,
    generate_draft, load_papers, load_headings
)
from gensurv.generate_overview import setup_coder

load_dotenv()


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", type=str, help="Title of the paper which you want to generate draft for")
    parser.add_argument("--retrieve_papers", action="store_true", help="Retrieve papers from Semantic Scholar")
    parser.add_argument("--max_papers", type=int, default=10, help="Maximum number of papers to retrieve")
    parser.add_argument("--papers_path", type=str, help="Path to the papers")
    parser.add_argument("--generate_headings", action="store_true", help="Generate headings")
    parser.add_argument("--headings_path", type=str, help="Path to the headings")
    parser.add_argument("--generate_draft", action="store_true", help="Generate draft")
    parser.add_argument("--output_path", type=Path, help="Output directory path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_name = f"{timestamp}_{args.title.replace(' ', '_')}"

    query = generate_query(args.title)
    client = OpenAI()
    coder = setup_coder(args.output_path / f"draft/{draft_name}.tex")


    if args.retrieve_papers:
        papers = retrieve_papers(
            query, args.max_papers,
            args.output_path / "semantic_scholar",
        )
    else:
        papers = load_papers(args.papers_path)

    if args.generate_headings:
        headings = generate_headings(papers)
    else:
        headings = load_headings(args.headings_path)

    structured_papers = classify_papers(headings, papers)
    overview = generate_overview(structured_papers)

    if args.generate_draft:
        generate_draft(overview)
