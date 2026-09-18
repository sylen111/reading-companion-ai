from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import os 

embedding_model = HuggingFaceEmbeddings(
    model_name = "BAAI/bge-base-en-v1.5"
)

def load_and_split_book(file_path: str | None, book_id: str, text: str | None = None):
    if text is None:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.create_documents([text])

    for chunk in chunks:
        chunk.metadata["book_id"] = book_id

    return chunks
