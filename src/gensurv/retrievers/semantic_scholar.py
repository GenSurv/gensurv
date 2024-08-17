import os
from pathlib import Path
import time

import backoff
from pydantic import BaseModel
import requests

from ..models import Paper, Author


class SemanticScholarError(Exception):
    pass


class SemanticScholarRetriever(BaseModel):
    output_dir: Path
    api_key: str = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key is None:
        raise SemanticScholarError("API key is required.")
    base_url: str = "https://api.semanticscholar.org/graph/v1"
    load_max_docs: int = 10
    sleep_time: int = 2

    def __init__(self, **data):
        super().__init__(**data)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def retrieve(
            self,
            query: str,
    ) -> list[Paper]:
        res = self.search_papers(query)
        self._sleep()
        if not res.get("data"):
            return []
        paper_ids = [paper["paperId"] for paper in res["data"]]
        papers = [self.retrieve_paper(paper_id) for paper_id in paper_ids]
        return papers

    @backoff.on_exception(backoff.expo, SemanticScholarError, max_time=3)
    def search_papers(self, query: str) -> dict:
        url = f"{self.base_url}/paper/search"
        params = {"query": query, "limit": self.load_max_docs}
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, params=params, headers=headers)
        return self.check_response_status(response)

    @backoff.on_exception(backoff.expo, SemanticScholarError, max_time=3)
    def retrieve_paper(self, paper_id: str, fields: str = "title,abstract,authors,venue,year") -> Paper:
        if (self.output_dir / f"{paper_id}.json").exists():
            with open(self.output_dir / f"{paper_id}.json") as f:
                return Paper.parse_raw(f.read())

        url = f"{self.base_url}/paper/{paper_id}"
        params = {"fields": fields}
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, params=params, headers=headers)
        response_dict = self.check_response_status(response)
        authors = [
            Author(id=author["authorId"], name=author["name"]) for author in response_dict.get("authors", [])
        ]
        paper = Paper(
            id=paper_id,
            title=response_dict.get("title", ""),
            abstract=response_dict.get("abstract", ""),
            venue=response_dict.get("venue", ""),
            year=response_dict.get("year", ""),
            authors=authors,
        )
        with open(self.output_dir / f"{paper_id}.json", "w") as f:
            f.write(paper.json())

        return paper

    def _sleep(self):
        time.sleep(self.sleep_time)
        return

    @staticmethod
    def check_response_status(response) -> dict:
        if response.status_code != 200:
            raise SemanticScholarError(f"Request failed with status code {response.status_code}: {response.text}")
        return response.json()
