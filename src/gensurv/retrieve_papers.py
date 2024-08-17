from .retrievers.semantic_scholar import SemanticScholarRetriever


def retrieve_papers(title: str, max_papers: int) -> list[str]:
    """

    :param title: A title of a paper which you want to generate an overview for.
    :param max_papers: Maximum number of papers to retrieve.
    :return:
    """
    retriever = SemanticScholarRetriever(load_max_docs=max_papers)
    query = title  # TODO: convert title to query
    docs = retriever.invoke(query)
    papers = [doc.page_content for doc in docs]
    return papers
