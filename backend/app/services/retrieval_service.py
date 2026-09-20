from dataclasses import dataclass

from app.services.embedding_service import embed_text
from app.services.vector_store import search


@dataclass(frozen=True)
class RetrievedChunk:
    document_id: int
    chunk_index: int
    text: str
    score: float


def retrieve(
    *,
    workspace_id: int,
    query: str,
    limit: int = 5,
) -> list[RetrievedChunk]:
    """Retrieve the most relevant chunks from one workspace."""
    if not query.strip():
        raise ValueError("Query cannot be empty")

    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    query_vector = embed_text(query)

    points = search(
        workspace_id=workspace_id,
        query_vector=query_vector,
        limit=limit,
    )

    results: list[RetrievedChunk] = []

    for point in points:
        payload = point.payload or {}

        results.append(
            RetrievedChunk(
                document_id=int(payload["document_id"]),
                chunk_index=int(payload["chunk_index"]),
                text=str(payload["text"]),
                score=float(point.score),
            )
        )

    return results
