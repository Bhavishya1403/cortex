import pytest

from app.services.document_chunker import (
    chunk_text,
    normalize_text,
)


def test_normalize_text():
    text = "  First   paragraph.  \n\n  Second   paragraph.  "

    result = normalize_text(text)

    assert result == "First paragraph.\n\nSecond paragraph."


def test_chunk_text_returns_indexed_chunks():
    text = "A " * 1200

    chunks = chunk_text(
        text,
        chunk_size=1000,
        chunk_overlap=200,
    )

    assert len(chunks) == 3
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]

    assert all(chunk.text for chunk in chunks)


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_text(
            "test",
            chunk_size=100,
            chunk_overlap=100,
        )


def test_chunk_text_rejects_empty_text():
    with pytest.raises(ValueError, match="no text"):
        chunk_text("   \n\n   ")
