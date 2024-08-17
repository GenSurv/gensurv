from retrievers.semantic_scholar import SemanticScholarRetriever


def retrieve_papers(title: str) -> list[str]:
    """

    :param title: A title of a paper which you want to generate an overview for.
    :return:
    """
    retriever = SemanticScholarRetriever()
    query = title  # TODO: convert title to query
    docs = retriever.invoke(query)
    papers = [doc.metadata for doc in docs]
    return papers
