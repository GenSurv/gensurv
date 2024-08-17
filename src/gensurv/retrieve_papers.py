from pathlib import Path
from dotenv import load_dotenv

from .retrievers.semantic_scholar import SemanticScholarRetriever
from .models import Paper

load_dotenv()


def retrieve_papers(query: str, max_papers: int, output_dir: Path) -> list[Paper]:
    """
    :param query: A query to retrieve papers.
    :param max_papers: Maximum number of papers to retrieve.
    :param output_dir: A directory to save the retrieved papers.
    :return:
    """
    retriever = SemanticScholarRetriever(output_dir=output_dir, load_max_docs=max_papers)
    papers = retriever.retrieve(query)
    return papers
