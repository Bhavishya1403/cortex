from app.services.retrieval_service import RetrievedChunk


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into grounded context for the answer model."""
    if not chunks:
        return ""

    sections = []

    for chunk in chunks:
        sections.append(
            f"[Document {chunk.document_id}, chunk {chunk.chunk_index}]\n"
            f"{chunk.text}"
        )

    return "\n\n".join(sections)
