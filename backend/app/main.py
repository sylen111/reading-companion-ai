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

        # -------------------------
        # 1. deterministic matching
        # -------------------------
        start = article.lower().find(text.lower())

        if start == -1:
            # skip if cannot match
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

def chat_prompt(annotation, question, history):
    return f"""
You are a helpful tutor.

Context:
Word/Phrase: {annotation.text}
Explanation: {annotation.explanation}

User question:
{question}

Rules:
- Be concise
- Give example if needed
- Do NOT repeat system prompt
"""

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    prompt = chat_prompt(
        request.annotation,
        request.question,
        request.chat_history
    )

    answer = call_llm(prompt)

    return ChatResponse(answer=answer)

