def extract_prompt(article: str) -> str:
    return f"""
You are an expert English teacher designing materials for B2 learners.

Task:
Select ONLY useful language items for learning.

IMPORTANT SELECTION RULES:

DO NOT include:
- basic prepositional phrases (e.g. "to X", "in X", "for several weeks")
- common time expressions
- simple location phrases
- sentences that are fully understandable at B2 level

ONLY include:
- idioms (non-literal meaning)
- strong collocations (e.g. "make a decision", "take a risk")
- advanced noun/verb phrases
- expressions slightly above B2 level

Classification rules:
- idiom = non-literal meaning ONLY
- chunk = useful collocation or advanced phrase

Return ONLY valid JSON:
- Max 10 items (reduce noise!)
- Must exist EXACTLY in text
- No overlapping spans

Output:
{{
  "annotations": [
    {{
      "id": "1",
      "text": "...",
      "type": "idiom | chunk",
      "explanation": "simple B2 explanation",
      "example": "simple example sentence"
    }}
  ]
}}

Text:
{article}
"""