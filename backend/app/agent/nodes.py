import json

from app.llm import call_llm, safe_parse_llm_output

from .memory import get_memory

def load_memory(state):

    memory = get_memory(
        state["annotation_type"],
        state["selected_text"]
    )

    state["category_fail_count"] = (
        memory["category_fail_count"]
    )

    state["item_fail_count"] = (
        memory["item_fail_count"]
    )

    return state

def planner_prompt(state):

    return f"""
You are an adaptive reading tutor.

Selected text: 
{state["selected_text"]}

Annotation type:
{state["annotation_type"]}

Category fail count:
{state["category_fail_count"]}

Item fail count:
{state["item_fail_count"]}

Decide:

1. explanation_depth:
   - simple
   - detailed

2. need_quiz:
   - true
   - false

Return JSON only.

Example:

{{
  "explanation_depth": "detailed",
  "need_quiz": true
}}
"""

def teaching_planner(state):

    raw = call_llm(planner_prompt(state))

    decision = safe_parse_llm_output(raw)

    state["explanation_depth"] = decision.get(
        "explanation_depth",
        "simple"
    )

    state["need_quiz"] = decision.get(
        "need_quiz",
        False
    )

    return state


def generate_quiz(state):

    state["quiz"] = f"""
What does "{state['selected_text']}" mean?
"""

    return state


def generate_answer(state):

    prompt = f"""
You are an adaptive reading tutor.

Phrase:
{state["selected_text"]}

Annotation type: 
{state["annotation_type"]}

Existing explanation:
{state["explanation"]}

User question:
{state["question"]}

Explanation depth:
{state["explanation_depth"]}

Conversation history: 
{state["chat_history"]}

User question: 
{state["question"]}

Rules:

- Focus only on the selected text. 
- Adapt explanation depth according to the strategy. 
- Avoid repeating previous explanations. 
- If the user asks for examples, generate different examples. - If the user asks for clarification, explain from a different perspective. 
- Use the surrounding context when appropriate. 
- Keep responses concise and conversational. 
- Do not mention internal reasoning or memory.
"""

    answer = call_llm(prompt)

    if state.get("quiz"):
        answer += f"\n\nQuick check:\n{state['quiz']}"

    state["answer"] = answer

    return state