from types import SimpleNamespace

import pytest

from app.services import retrieval_service


def test_retrieve_embeds_query_and_returns_chunks(monkeypatch):
    captured = {}

    def fake_embed_text(query):
        captured["query"] = query
        return [0.1] * 768

    def fake_search(*, workspace_id, query_vector, limit):
        captured["workspace_id"] = workspace_id
        captured["query_vector"] = query_vector
        captured["limit"] = limit

        return [
            SimpleNamespace(
                score=0.91,
                payload={
                    "document_id": 12,
                    "chunk_index": 3,
                    "text": "Cortex retrieval test.",
                },
            )
        ]

    monkeypatch.setattr(retrieval_service, "embed_text", fake_embed_text)
    monkeypatch.setattr(retrieval_service, "search", fake_search)

    results = retrieval_service.retrieve(
        workspace_id=42,
        query="What is Cortex?",
        limit=3,
    )

    assert captured["query"] == "What is Cortex?"
    assert captured["workspace_id"] == 42
    assert captured["query_vector"] == [0.1] * 768
    assert captured["limit"] == 3

    assert len(results) == 1
    assert results[0].document_id == 12
    assert results[0].chunk_index == 3
    assert results[0].text == "Cortex retrieval test."
    assert results[0].score == 0.91


def test_retrieve_rejects_empty_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        retrieval_service.retrieve(
            workspace_id=42,
            query="   ",
        )


def test_retrieve_rejects_invalid_limit():
    with pytest.raises(ValueError, match="limit must be greater than 0"):
        retrieval_service.retrieve(
            workspace_id=42,
            query="What is Cortex?",
            limit=0,
        )
