import os
import time
from typing import List, Any, Optional

import requests
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig, ensure_config

from ..models import Paper, Author


class SemanticScholarError(Exception):
    pass


class SemanticScholarRetriever(BaseRetriever):
    api_key: str = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key is None:
        raise SemanticScholarError("API key is required.")
    base_url = "https://api.semanticscholar.org/graph/v1"
    load_max_docs: int = 10
    sleep_time: int = 2

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun,
            **kwargs: Any,
    ) -> List[Paper]:
        res = self.search_papers(query)
        self._sleep()
        if not res.get("data"):
            return []
        paper_ids = [paper["paperId"] for paper in res["data"]]
        papers = [self.retrieve_paper(paper_id, **kwargs) for paper_id in paper_ids]
        return papers

    def search_papers(self, query: str) -> dict:
        url = f"{self.base_url}/paper/search"
        params = {"query": query, "limit": self.load_max_docs}
        headers = {"x-api-key": self.api_key}
        response = requests.get(url, params=params, headers=headers)
        return self.check_response_status(response)

    def retrieve_paper(self, paper_id: str, fields: str = "title,abstract,authors,venue,year") -> Paper:
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
        return paper

    def _sleep(self):
        time.sleep(self.sleep_time)
        return

    @staticmethod
    def check_response_status(response) -> dict:
        if response.status_code != 200:
            raise SemanticScholarError(f"Request failed with status code {response.status_code}: {response.text}")
        return response.json()

    def invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> List[Paper]:
        config = ensure_config(config)
        return self.get_relevant_documents(
            input,
            callbacks=config.get("callbacks"),
            tags=config.get("tags"),
            metadata=config.get("metadata"),
            run_name=config.get("run_name"),
            **kwargs,
        )
