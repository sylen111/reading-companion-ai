from .vector_store import get_vector_store


def search_book(query: str, book_id: str, k: int = 3):
    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query,
        k=k,
        filter={"book_id": book_id}
    )

    return results


if __name__ == "__main__":
    query = "Why did John become less lonely?"
    book_id = "book.txt"

    results = search_book(
        query=query,
        book_id=book_id,
        k=3
    )

    print(f"Query: {query}")
    print(f"Book: {book_id}")
    print(f"Retrieved {len(results)} chunks\n")

    for i, result in enumerate(results, start=1):
        print("=" * 60)
        print(f"Result {i}")
        print("Metadata:", result.metadata)
        print("Content:")
        print(result.page_content)
        print()