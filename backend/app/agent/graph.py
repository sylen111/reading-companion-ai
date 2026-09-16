from langgraph.graph import StateGraph
from langgraph.constants import START, END
from .state import ReadingState

from .nodes import (
    load_memory,
    teaching_planner,
    generate_quiz,
    generate_answer,
    retrieve_context,
)

builder = StateGraph(ReadingState)

builder.add_node("load_memory", load_memory)
builder.add_node("planner", teaching_planner)
builder.add_node("quiz", generate_quiz)
builder.add_node("answer", generate_answer)
builder.add_node("rag", retrieve_context)

builder.add_edge(START, "load_memory")
builder.add_edge("load_memory", "planner")

def route_after_planner(state):

    if state["need_rag"]:
        return "rag"

    if state["need_quiz"]:
        return "quiz"

    return "answer"


builder.add_conditional_edges(
    "planner",
    route_after_planner,
    {
        "rag": "rag",
        "quiz": "quiz",
        "answer": "answer",
    }
)

builder.add_edge("rag", "answer")
builder.add_edge("quiz", "answer")
builder.add_edge("answer", END)

graph = builder.compile()