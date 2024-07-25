import os
import time
from typing import List, Any

import requests
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class SemanticScholarError(Exception):
    pass


class SemanticScholarRetriever(BaseRetriever):
    api_key: str = os.environ.get('SEMANTIC_SCHOLAR_API_KEY')
    if api_key is None:
        raise SemanticScholarError("API key is required.")
    base_url = 'https://api.semanticscholar.org/graph/v1'
    load_max_docs: int = 10
    sleep_time: int = 2

    def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun,
            **kwargs: Any,
    ) -> List[Document]:
        res = self.search_papers(query)
        self._sleep()
        if not res.get('data'):
            return []
        paper_ids = [paper['paperId'] for paper in res['data']]
        papers = []
        for paper_id in paper_ids:
            paper = self.retrieve_paper(paper_id, **kwargs)
            papers.append(paper)
            self._sleep()
        docs = []
        for paper in papers:
            authors = ", ".join([
                author.get("name", "")
                for author in paper.get("authors", [])
            ])
            doc = Document(
                page_content="\n".join([
                    f"Title: {paper.get('title','')}\n"
                    f"Authors: {authors}\n"
                    f"Abstract: {paper.get('abstract', '')}\n"
                    f"Venue: {paper.get('venue', '')}\n"
                    f"Year: {paper.get('year', '')}\n"
                ]),
                metadata=paper
            )
            docs.append(doc)
        return docs

    def search_papers(self, query: str) -> dict:
        url = f'{self.base_url}/paper/search'
        params = {'query': query, 'limit': self.load_max_docs}
        headers = {'x-api-key': self.api_key}
        response = requests.get(url, params=params, headers=headers)
        return self.check_response_status(response)

    def retrieve_paper(self, paper_id: str, fields: str = "title,abstract,authors,venue,year") -> dict:
        url = f'{self.base_url}/paper/{paper_id}'
        params = {"fields": fields}
        headers = {'x-api-key': self.api_key}
        response = requests.get(url, params=params, headers=headers)
        return self.check_response_status(response)

    def _sleep(self):
        time.sleep(self.sleep_time)
        return

    @staticmethod
    def check_response_status(response):
        if response.status_code != 200:
            raise SemanticScholarError(f"Request failed with status code {response.status_code}: {response.text}")
        return response.json()
