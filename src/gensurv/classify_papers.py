from .models import Paper


def classify_papers(headings: list[str], papers: list[Paper]) -> dict[str, list[Paper]]:
    ...
