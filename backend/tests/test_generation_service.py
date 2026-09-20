from types import SimpleNamespace

import pytest

from app.services import generation_service


def test_generate_answer_returns_model_text(monkeypatch):
    captured = {}

    def fake_generate_content(*, model, contents):
        captured["model"] = model
        captured["contents"] = contents
        return SimpleNamespace(text="Cortex is a RAG application.")

    monkeypatch.setattr(
        generation_service.client.models,
        "generate_content",
        fake_generate_content,
    )

    answer = generation_service.generate_answer(
        query="What is Cortex?",
        context="[Document 1, chunk 0]\nCortex is a RAG application.",
    )

    assert answer == "Cortex is a RAG application."
    assert captured["model"] == generation_service.GENERATION_MODEL
    assert "What is Cortex?" in captured["contents"]
    assert "Cortex is a RAG application." in captured["contents"]


def test_generate_answer_rejects_empty_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        generation_service.generate_answer(
            query=" ",
            context="Some context.",
        )


def test_generate_answer_rejects_empty_context():
    with pytest.raises(ValueError, match="Context cannot be empty"):
        generation_service.generate_answer(
            query="What is Cortex?",
            context=" ",
        )


def test_generate_answer_rejects_empty_model_response(monkeypatch):
    def fake_generate_content(*, model, contents):
        return SimpleNamespace(text="")

    monkeypatch.setattr(
        generation_service.client.models,
        "generate_content",
        fake_generate_content,
    )

    with pytest.raises(
        ValueError,
        match="Generation provider returned an empty answer",
    ):
        generation_service.generate_answer(
            query="What is Cortex?",
            context="Cortex is a RAG application.",
        )


def test_generate_answer_includes_critic_feedback(monkeypatch):
    captured = {}

    def fake_generate_content(*, model, contents):
        captured["contents"] = contents
        return SimpleNamespace(text="Corrected answer.")

    monkeypatch.setattr(
        generation_service.client.models,
        "generate_content",
        fake_generate_content,
    )

    answer = generation_service.generate_answer(
        query="What is Cortex?",
        context="[Document 1, chunk 0]\nCortex is a RAG application.",
        critic_feedback="The answer must stay within the provided context.",
    )

    assert answer == "Corrected answer."
    assert "PREVIOUS ANSWER FEEDBACK:" in captured["contents"]
    assert "The answer must stay within the provided context." in captured["contents"]
    assert "Revise the answer to address this feedback." in captured["contents"]
