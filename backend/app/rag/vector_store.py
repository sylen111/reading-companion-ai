from langchain_chroma import Chroma
from .ingestion import load_and_split_book, embedding_model
import os

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "books"

def get_vector_store():
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding_model,
        persist_directory=CHROMA_PATH
    )

def create_vector_store(chunks):
    vector_store = get_vector_store()

    vector_store.add_documents(chunks)

    return vector_store


def book_exists(book_id: str):
    vector_store = get_vector_store()

    results = vector_store.get(
        where={"book_id": book_id},
        limit=1
    )

    return len(results["ids"]) > 0

if __name__ == "__main__":
    book_id = os.path.basename(file_path)
    print(book_id)

    if book_exists(book_id):
        print(f"Book '{book_id}' already exists.")
    else:
        chunks = load_and_split_book(file_path, book_id)
        create_vector_store(chunks)
        print(f"Stored {len(chunks)} chunks in Chroma.")