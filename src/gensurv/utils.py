from pathlib import Path

from .models import Paper


def load_papers(papers_path: Path) -> list[Paper]:
    ...


def load_headings(headings_path: Path) -> list[str]:
    ...
