from pathlib import Path

from .models import Paper


def load_papers(papers_path: Path) -> list[Paper]:
    ...


def load_headings(headings_path: Path) -> list[str]:
    ...

def format_bibtex(bibtex: str) -> str:
    # Remove any newline characters and extra spaces
    bibtex = ' '.join(bibtex.split())
    # Escape any backslashes and double quotes
    bibtex = bibtex.replace('\\', '\\\\').replace('"', '\\"')
    return bibtex
