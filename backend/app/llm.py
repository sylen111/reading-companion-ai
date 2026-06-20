import requests
import json
import re
from fastapi import HTTPException

OLLAMA_URL = "http://localhost:11434/api/generate"


# -------------------------
# 1. CALL LLM (FIXED)
# -------------------------
def call_llm(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3:latest",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()

        # IMPORTANT: always return STRING
        return response.json().get("response", "")

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to LLaMA3"
        )


# -------------------------
# 2. PROMPT (UNCHANGED BUT CLEAN)
# -------------------------
def extract_prompt(article: str) -> str:
    return f"""
You are an NLP assistant.

Task:
Extract idioms and difficult chunks from the text.

Rules:
- Return ONLY valid JSON
- No explanation
- Max 15 items
- No overlapping spans
- Must include: id, text, type, start, end, explanation

Output format:
{{
  "annotations": [
    {{
      "id": "1",
      "text": "...",
      "type": "idiom | chunk",
      "start": 0,
      "end": 10,
      "explanation": "..."
    }}
  ]
}}

Text:
{article}
"""


# -------------------------
# 3. SAFE PARSER (FIXED)
# -------------------------
def safe_parse_llm_output(text: str):
    # Case 1: already dict (future-proof)
    if isinstance(text, dict):
        return text

    # Case 2: normal JSON string
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # fallback: extract JSON block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))

    raise ValueError(f"Invalid LLM output: {text}")