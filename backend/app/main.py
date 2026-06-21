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


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.llm import call_llm, safe_parse_llm_output
from app.prompts import extract_prompt
from app.annotation import Annotation, AnnotationType
from app.analyze import AnalyzeRequest, AnalyzeResponse
from app.chat import ChatRequest, ChatResponse
from app.agent.graph import graph
from app.agent.memory import (get_memory, increase_fail_count)

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
    text = annotation.text.lower() 
    ann_type = annotation.type.value
    memory = get_memory(ann_type, text)

    state = {
        "selected_text": annotation.text,
        "annotation_type": ann_type,
        "explanation": annotation.explanation,
        "question": request.question,
        "chat_history": request.chat_history,
        "fail_count": memory["category_fail_count"],
        "item_fail_count": memory["item_fail_count"],
        "explanation_depth": "simple",
        "need_quiz": False,
        "quiz": None,
        "answer": None,
    }

    result = graph.invoke(state)

    increase_fail_count(ann_type, text)

    return ChatResponse(
        answer=result["answer"]
    )

