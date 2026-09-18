from .vector_store import get_vector_store


def search_book(query: str, book_id: str, k: int = 3):
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query,
        k=k,
        filter={"book_id": book_id}
    )

    return results
