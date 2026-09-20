from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.context_builder import build_context
from app.services.critic_service import CriticResult, verify_answer
from app.services.generation_service import generate_answer
from app.services.retrieval_service import retrieve


MAX_GENERATION_ATTEMPTS = 2


class RAGState(TypedDict, total=False):
    workspace_id: int
    query: str
    retrieval_limit: int
    context: str
    answer: str
    grounded: bool
    critic_feedback: str
    generation_attempts: int


def retrieve_node(state: RAGState) -> dict:
    chunks = retrieve(
        workspace_id=state["workspace_id"],
        query=state["query"],
        limit=state.get("retrieval_limit", 5),
    )

    return {
        "context": build_context(chunks),
    }


def generate_node(state: RAGState) -> dict:
    answer = generate_answer(
        query=state["query"],
        context=state["context"],
        critic_feedback=state.get("critic_feedback"),
    )

    attempts = state.get("generation_attempts", 0) + 1

    return {
        "answer": answer,
        "generation_attempts": attempts,
    }


def critic_node(state: RAGState) -> dict:
    result: CriticResult = verify_answer(
        query=state["query"],
        context=state["context"],
        answer=state["answer"],
    )

    return {
        "grounded": result.grounded,
        "critic_feedback": result.feedback,
    }


def route_after_critic(state: RAGState) -> str:
    if state.get("grounded", False):
        return "finish"

    if state.get("generation_attempts", 0) >= MAX_GENERATION_ATTEMPTS:
        return "finish"

    return "retry"


def build_rag_graph():
    graph = StateGraph(RAGState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("critic", critic_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "retry": "generate",
            "finish": END,
        },
    )

    return graph.compile()
