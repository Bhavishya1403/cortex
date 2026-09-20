from app.services.context_builder import build_context
from app.services.retrieval_service import RetrievedChunk


def test_build_context_formats_chunks():
    chunks = [
        RetrievedChunk(
            document_id=10,
            chunk_index=0,
            text="First chunk.",
            score=0.95,
        ),
        RetrievedChunk(
            document_id=10,
            chunk_index=1,
            text="Second chunk.",
            score=0.87,
        ),
    ]

    assert build_context(chunks) == (
        "[Document 10, chunk 0]\n"
        "First chunk.\n\n"
        "[Document 10, chunk 1]\n"
        "Second chunk."
    )


def test_build_context_empty_chunks():
    assert build_context([]) == ""
