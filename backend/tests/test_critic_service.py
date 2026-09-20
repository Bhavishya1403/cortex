from types import SimpleNamespace

import pytest

from app.services import critic_service


def test_verify_answer_returns_structured_result(monkeypatch):
    captured = {}

    def fake_generate_content(*, model, contents, config):
        captured["model"] = model
        captured["contents"] = contents
        captured["config"] = config

        return SimpleNamespace(
            text='{"grounded": true, "feedback": "The answer is supported by the context."}'
        )

    monkeypatch.setattr(
        critic_service.client.models,
        "generate_content",
        fake_generate_content,
    )

    result = critic_service.verify_answer(
        query="What is Cortex?",
        context="[Document 1, chunk 0]\nCortex is a RAG application.",
        answer="Cortex is a RAG application.",
    )

    assert result.grounded is True
    assert result.feedback == "The answer is supported by the context."

    assert captured["model"] == critic_service.CRITIC_MODEL
    assert "What is Cortex?" in captured["contents"]
    assert "Cortex is a RAG application." in captured["contents"]
    assert captured["config"].response_mime_type == "application/json"
    assert captured["config"].response_schema is critic_service.CriticResult


def test_verify_answer_rejects_empty_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        critic_service.verify_answer(
            query=" ",
            context="Some context.",
            answer="Some answer.",
        )


def test_verify_answer_rejects_empty_context():
    with pytest.raises(ValueError, match="Context cannot be empty"):
        critic_service.verify_answer(
            query="What is Cortex?",
            context=" ",
            answer="Some answer.",
        )


def test_verify_answer_rejects_empty_answer():
    with pytest.raises(ValueError, match="Answer cannot be empty"):
        critic_service.verify_answer(
            query="What is Cortex?",
            context="Some context.",
            answer=" ",
        )


def test_verify_answer_rejects_empty_model_response(monkeypatch):
    def fake_generate_content(*, model, contents, config):
        return SimpleNamespace(text="")

    monkeypatch.setattr(
        critic_service.client.models,
        "generate_content",
        fake_generate_content,
    )

    with pytest.raises(
        ValueError,
        match="Critic provider returned an empty response",
    ):
        critic_service.verify_answer(
            query="What is Cortex?",
            context="Cortex is a RAG application.",
            answer="Cortex is a RAG application.",
        )
