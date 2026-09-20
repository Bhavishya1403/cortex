from app.services import rag_graph
from app.services.retrieval_service import RetrievedChunk


def fake_retrieve(*, workspace_id, query, limit):
    return [
        RetrievedChunk(
            document_id=10,
            chunk_index=0,
            text="Cortex is an enterprise RAG application.",
            score=0.95,
        )
    ]


def test_rag_graph_finishes_when_answer_is_grounded(monkeypatch):
    calls = []

    def fake_generate_answer(*, query, context, critic_feedback=None):
        calls.append(("generate", critic_feedback))
        return "Cortex is an enterprise RAG application."

    def fake_verify_answer(*, query, context, answer):
        calls.append(("critic", answer))
        return rag_graph.CriticResult(
            grounded=True,
            feedback="Supported by context.",
        )

    monkeypatch.setattr(rag_graph, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag_graph, "generate_answer", fake_generate_answer)
    monkeypatch.setattr(rag_graph, "verify_answer", fake_verify_answer)

    graph = rag_graph.build_rag_graph()

    result = graph.invoke(
        {
            "workspace_id": 2,
            "query": "What is Cortex?",
        }
    )

    assert result["grounded"] is True
    assert result["generation_attempts"] == 1
    assert calls == [
        ("generate", None),
        ("critic", "Cortex is an enterprise RAG application."),
    ]


def test_rag_graph_retries_with_critic_feedback(monkeypatch):
    calls = []
    critic_results = iter(
        [
            rag_graph.CriticResult(
                grounded=False,
                feedback="The answer contains an unsupported claim.",
            ),
            rag_graph.CriticResult(
                grounded=True,
                feedback="The revised answer is supported.",
            ),
        ]
    )

    def fake_generate_answer(*, query, context, critic_feedback=None):
        calls.append(("generate", critic_feedback))

        if critic_feedback is None:
            return "Answer attempt 1"

        return "Corrected answer"

    def fake_verify_answer(*, query, context, answer):
        calls.append(("critic", answer))
        return next(critic_results)

    monkeypatch.setattr(rag_graph, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag_graph, "generate_answer", fake_generate_answer)
    monkeypatch.setattr(rag_graph, "verify_answer", fake_verify_answer)

    graph = rag_graph.build_rag_graph()

    result = graph.invoke(
        {
            "workspace_id": 2,
            "query": "What is Cortex?",
        }
    )

    assert result["grounded"] is True
    assert result["generation_attempts"] == 2
    assert result["answer"] == "Corrected answer"

    assert calls == [
        ("generate", None),
        ("critic", "Answer attempt 1"),
        (
            "generate",
            "The answer contains an unsupported claim.",
        ),
        ("critic", "Corrected answer"),
    ]


def test_rag_graph_stops_after_max_generation_attempts(monkeypatch):
    calls = []

    def fake_generate_answer(*, query, context, critic_feedback=None):
        calls.append(("generate", critic_feedback))
        return "Unsupported answer."

    def fake_verify_answer(*, query, context, answer):
        calls.append(("critic", answer))
        return rag_graph.CriticResult(
            grounded=False,
            feedback="Unsupported by context.",
        )

    monkeypatch.setattr(rag_graph, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag_graph, "generate_answer", fake_generate_answer)
    monkeypatch.setattr(rag_graph, "verify_answer", fake_verify_answer)

    graph = rag_graph.build_rag_graph()

    result = graph.invoke(
        {
            "workspace_id": 2,
            "query": "What is Cortex?",
        }
    )

    assert result["grounded"] is False
    assert result["generation_attempts"] == rag_graph.MAX_GENERATION_ATTEMPTS

    assert calls == [
        ("generate", None),
        ("critic", "Unsupported answer."),
        ("generate", "Unsupported by context."),
        ("critic", "Unsupported answer."),
    ]
