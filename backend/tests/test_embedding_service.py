from types import SimpleNamespace

import pytest

from app.services import embedding_service


def test_embed_text_returns_expected_vector(monkeypatch):
    fake_vector = [0.1] * 768

    fake_response = SimpleNamespace(
        embeddings=[
            SimpleNamespace(values=fake_vector),
        ]
    )

    def fake_embed_content(**kwargs):
        assert kwargs["model"] == "gemini-embedding-2"
        assert kwargs["contents"] == "Cortex test"
        assert kwargs["config"].output_dimensionality == 768

        return fake_response

    monkeypatch.setattr(
        embedding_service.client.models,
        "embed_content",
        fake_embed_content,
    )

    vector = embedding_service.embed_text("Cortex test")

    assert len(vector) == 768
    assert vector == fake_vector


def test_embed_text_rejects_empty_text():
    with pytest.raises(ValueError, match="empty text"):
        embedding_service.embed_text("   ")


def test_embed_text_rejects_wrong_dimension(monkeypatch):
    fake_response = SimpleNamespace(
        embeddings=[
            SimpleNamespace(values=[0.1] * 100),
        ]
    )

    monkeypatch.setattr(
        embedding_service.client.models,
        "embed_content",
        lambda **kwargs: fake_response,
    )

    with pytest.raises(ValueError, match="Expected 768"):
        embedding_service.embed_text("Cortex test")
