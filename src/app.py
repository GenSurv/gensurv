import gradio as gr
import pandas as pd
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from gensurv.generate_headings import classify_papers_batch
from gensurv.retrievers.semantic_scholar import SemanticScholarRetriever

retriever = SemanticScholarRetriever(output_dir=Path("../data/semantic_scholar"), sleep_time=5)


def classify(file_path: Path):
    df = pd.read_csv(file_path, delimiter="\t")
    valid_data = df[df["headlines_section_title"].notna() & df["paper_id"].notna()]
    headings = valid_data["headlines_section_title"].tolist()
    paper_ids = valid_data["paper_id"].tolist()
    papers = [retriever.retrieve_paper(pid) for pid in paper_ids]
    structured_papers = classify_papers_batch(papers, headings)
    simple_structured = {heading: [p.title for p in papers] for heading, papers in structured_papers.items()}
    return simple_structured


iface = gr.Interface(
    fn=classify,
    inputs=gr.File(label="TSVファイルをアップロード"),
    outputs=gr.JSON(label="構造化Papers"),
    title="論文を見出しに割り当て",
    description="TSVファイルをアップロードすると、各見出しに対して割り当てられるべきPaper.titleを表示します。"
)

iface.launch()
