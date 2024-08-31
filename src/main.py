from datetime import datetime
from pathlib import Path
import shutil

from dotenv import load_dotenv

from gensurv import (
    generate_query, retrieve_papers, generate_headings, classify_papers, generate_overview,
    generate_draft, load_papers, load_headings
)

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
    parser.add_argument("--output_path", type=Path, help="Output directory path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    draft_name = f"{timestamp}_{args.title.replace(' ', '_')}"
    output_dir = (args.output_path / draft_name).resolve()

    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    latex_dir = data_dir / "latex"
    shutil.copytree(latex_dir, output_dir)

    query = generate_query(args.title)

    if args.retrieve_papers:
        print("Retrieving papers from Semantic Scholar...")
        papers = retrieve_papers(
            query, args.max_papers,
            args.output_path / "semantic_scholar",
        )
    else:
        print("Loading papers...")
        papers = load_papers(args.papers_path)

    if args.generate_headings:
        print("Generating headings...")
        # TODO: move classify_papers() from generate_headings.py to classify_papers.py
        # headings = generate_headings(papers)
        structured_papers = generate_headings(papers)
    else:
        print("Loading headings...")
        headings = load_headings(args.headings_path)
        structured_papers = classify_papers(headings, papers)

    print("Generating overview...")
    overview = generate_overview(structured_papers, args.title)

    print("Generating draft...")
    generate_draft(overview, papers, output_dir)
