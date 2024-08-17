from dotenv import load_dotenv
load_dotenv()

from gensurv import retrieve_papers, generate_headings, classify_papers, generate_overview, generate_draft, load_papers, load_headings


def main(data_path, output_path):
    import pandas as pd
    df = pd.read_csv(data_path)
    df.to_csv(output_path, index=False)


def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--title', type=str)
    parser.add_argument('--retrieve_papers', action='store_true')
    parser.add_argument('--max_papers', type=int, default=10)
    parser.add_argument('--papers_path', type=str)
    parser.add_argument('--generate_headings', action='store_true')
    parser.add_argument('--headings_path', type=str)
    parser.add_argument('--generate_draft', action='store_true')
    parser.add_argument('--output_path', type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.retrieve_papers:
        papers = retrieve_papers(args.title, args.max_papers)
    else:
        papers = load_papers(args.papers_path)

    if args.generate_headings:
        headings = generate_headings(papers)
    else:
        headings = load_headings(args.headings_path)

    structured_papers = classify_papers(headings, papers)
    overview = generate_overview(structured_papers)

    if args.generate_draft:
        draft = generate_draft(overview)



