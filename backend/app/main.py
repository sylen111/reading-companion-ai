# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List
# import requests


# app = FastAPI(title="Reading Companion AI")

# class Message(BaseModel):
#     role: str
#     content: str

# class ChatRequest(BaseModel):
#     messages: List[Message]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def root():
#     return {"message": "Reading Companion API"}

# @app.post("/ask")
# def ask(request: ChatRequest):
#     prompt = request.messages[-1].content
    
#     try:
#         response = requests.post(
#             "http://localhost:11434/api/generate",
#             json={
#                 "model": "llama3:latest",
#                 "prompt": prompt,
#                 "stream": False
#             },
#             timeout=60
#         )

#         response.raise_for_status()

#         return {
#             "response": response.json().get("response", "")
#         }

#     except requests.exceptions.RequestException:
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to connect to LLaMA3"
#         )


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.llm import call_llm, safe_parse_llm_output
from app.prompts import extract_prompt
from app.annotation import Annotation, AnnotationType
from app.analyze import AnalyzeRequest, AnalyzeResponse
from app.chat import ChatRequest, ChatResponse
from app.agent.graph import graph
from app.agent.memory import (get_memory, increase_fail_count)
from app.rag.ingestion import load_and_split_book
from app.rag.vector_store import create_vector_store
import uuid

app = FastAPI(title="Reading Companion AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Reading Companion API"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):

    prompt = extract_prompt(request.article)

    raw = call_llm(prompt)

    data = safe_parse_llm_output(raw)

    annotations = []

    article = request.article

    for i, item in enumerate(data.get("annotations", [])):

        text = item["text"]

        start = article.lower().find(text.lower())

        if start == -1:
            continue

        end = start + len(text)

        annotations.append(
            Annotation(
                id=str(i + 1),
                text=text,
                type=AnnotationType(item["type"]),
                start=start,
                end=end,
                explanation=item.get("explanation", "")
            )
        )

    return AnalyzeResponse(annotations=annotations)



@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    annotation = request.annotation

    # --------------------------------
    # Annotation mode
    # --------------------------------
    if request.use_annotation and annotation:

        text = annotation.text.lower()
        ann_type = annotation.type.value

        memory = get_memory(
            ann_type,
            text
        )

        selected_text = annotation.text
        explanation = annotation.explanation

        fail_count = memory["category_fail_count"]
        item_fail_count = memory["item_fail_count"]

    # --------------------------------
    # Normal book chat mode
    # --------------------------------
    else:

        text = ""
        ann_type = ""

        selected_text = ""
        explanation = ""

        fail_count = 0
        item_fail_count = 0

    state = {
        "selected_text": selected_text,
        "annotation_type": ann_type,
        "explanation": explanation,
        "use_annotation": request.use_annotation,

        "question": request.question,
        "chat_history": request.chat_history,

        "book_id": request.book_id,

        "fail_count": fail_count,
        "item_fail_count": item_fail_count,

        "explanation_depth": "simple",
        "need_quiz": False,

        "need_rag": False,
        "rag_context": "",

        "quiz": None,
        "answer": None,
    }

    result = graph.invoke(state)

    # Only update learning memory in annotation mode
    if request.use_annotation and annotation:
        increase_fail_count(
            ann_type,
            text
        )

    return ChatResponse(
        answer=result["answer"]
    )


@app.post("/books/upload")
async def upload_book(file: UploadFile = File(...)):

    # 1. Check file type
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported."
        )

    # 2. Read file
    content = await file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded."
        )

    # 3. Basic validation
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded book is empty."
        )

    # 4. Create book ID
    book_id = str(uuid.uuid4())

    pages = split_into_pages(text)

    chunks = load_and_split_book(
        file_path=None,
        book_id=book_id,
        text=text
    )

    create_vector_store(chunks)

    return {
        "book_id": book_id,
        "filename": file.filename,
        "characters": len(text),
        "pages": pages,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "message": "Book uploaded successfully."
    }

def split_into_pages(text: str, max_chars: int = 3000):
    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip()
    ]

    pages = []
    current_page = ""

    for paragraph in paragraphs:

        if len(current_page) + len(paragraph) + 2 <= max_chars:
            current_page += paragraph + "\n\n"

        else:
            if current_page:
                pages.append(current_page.strip())

            current_page = paragraph + "\n\n"

    if current_page:
        pages.append(current_page.strip())

    return pages