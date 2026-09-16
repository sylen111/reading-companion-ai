from .retriever import search_book
from app.llm import call_llm


def ask_book(
    query: str,
    book_id: str,
    k: int = 3
):
    # 1. Retrieve relevant book passages
    results = search_book(
        query=query,
        book_id=book_id,
        k=k
    )

    # 2. Build context from retrieved chunks
    context = "\n\n".join(
        result.page_content
        for result in results
    )

    # 3. Build RAG prompt
    prompt = f"""
You are a reading companion.

Answer the user's question using only the book passages provided below.

If the passages do not contain enough information to answer the question,
say that the information is not available in the retrieved passages.

Book passages:
{context}

User question:
{query}

Answer:
"""

    # 4. Send prompt to Ollama
    answer = call_llm(prompt)

    return {
        "answer": answer,
        "sources": results
    }


if __name__ == "__main__":
    query = "Why did John become less lonely?"
    book_id = "book.txt"

    result = ask_book(
        query=query,
        book_id=book_id
    )

    print("\n====================")
    print("ANSWER")
    print("====================")
    print(result["answer"])

    print("\n====================")
    print("SOURCES")
    print("====================")

    for i, source in enumerate(result["sources"], start=1):
        print(f"\n--- Source {i} ---")
        print(source.page_content)
        print("Metadata:", source.metadata)