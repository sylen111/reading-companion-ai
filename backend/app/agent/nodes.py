import json

from app.llm import call_llm, safe_parse_llm_output
from app.rag.retriever import search_book

from .memory import get_memory

def load_memory(state):

    if not state.get("selected_text"):
        state["category_fail_count"] = 0
        state["item_fail_count"] = 0
        return state

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
        
        User question:
        {state["question"]}

        Selected text:
        {state.get("selected_text", "")}

        Annotation type:
        {state.get("annotation_type", "")}

        Category fail count:
        {state.get("category_fail_count", 0)}

        Item fail count:
        {state.get("item_fail_count", 0)}

        Decide:

        1. explanation_depth:
        - simple
        - detailed

        2. need_quiz:
        - true
        - false

        3. need_rag:
        - true if the question requires information from the book
        - false if the question can be answered using the selected text alone

        Use these rules for need_rag:

        - Set need_rag to true if the user asks about events,
        characters, relationships, or information that may require
        looking at other parts of the book.

        - Set need_rag to true for questions such as:
        "Why did John become less lonely?"
        "What happened earlier?"
        "Has John met Sarah before?"
        "Why does John dislike Sarah?"

        - Set need_rag to false for questions that can be answered
        directly from the selected text, such as:
        "What does this word mean?"
        "What does this phrase mean?"
        "Can you explain this sentence?"
        
        Return JSON only.

        Example:

        {{
        "explanation_depth": "detailed",
        "need_quiz": true，
        "need_rag": true
        }}
    """

def teaching_planner(state):

    selected_text = state.get("selected_text", "")
    question = state.get("question", "")
    use_annotation = state.get("use_annotation", False)

    if not use_annotation :
        state["explanation_depth"] = "simple"
        state["need_quiz"] = False
        state["need_rag"] = should_use_rag(question)
        return state

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

    state["need_rag"] = False

    return state

def generate_quiz(state):

    state["quiz"] = f"""
What does "{state['selected_text']}" mean?
"""

    return state


def generate_answer(state):
    selected_text = state.get("selected_text", "")
    rag_context = state.get("rag_context", "")
    question = state.get("question", "")
    use_annotation = state.get("use_annotation", False)

    if use_annotation:
        prompt = f"""
You are an adaptive reading tutor.

The user selected this expression from the book:

"{selected_text}"

Annotation type:
{state.get("annotation_type", "")}

Existing explanation:
{state.get("explanation", "")}

User question:
{question}

Explanation depth:
{state.get("explanation_depth", "simple")}

Conversation history:
{state.get("chat_history", [])}

Rules:
- Focus on the selected expression.
- Explain it clearly and concisely.
- Adapt the explanation depth.
- Avoid repeating previous explanations.
- If the user asks for examples, give different examples.
- Keep the response conversational.
"""
    else:
        prompt = f"""
You are a reading companion.

The user is having a normal conversation about the book.

User question:
{question}

Book context:
{rag_context}

Conversation history:
{state.get("chat_history", [])}

Rules:
- Answer the user's question naturally.
- Do not talk about selected text, annotations, or annotation types.
- If book context is provided, use it when relevant.
- If the book context does not contain enough information, say so.
- For casual messages such as "hi", "hello", or "thanks", respond naturally.
- Keep the response concise and conversational.
"""

    answer = call_llm(prompt)

    # Only add quiz when there is an actual selected annotation
    if selected_text and state.get("quiz"):
        answer += f"\n\nQuick check:\n{state['quiz']}"

    state["answer"] = answer
    return state

def retrieve_context(state):

    results = search_book(
        query=state["question"],
        book_id=state["book_id"],
        k=3
    )

    context = "\n\n".join(
        result.page_content
        for result in results
    )

    state["rag_context"] = context

    return state

def should_use_rag(question: str) -> bool:

    #rule-based for local LLM
    rag_keywords = [
        "why",
        "what happened",
        "who",
        "where",
        "when",
        "how",
        "character",
        "relationship",
        "earlier",
        "before",
        "previously",
        "later",
        "story",
        "book"
    ]

    question_lower = question.lower()

    return any(
        keyword in question_lower
        for keyword in rag_keywords
    )