from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings


COLLECTION_NAME = "cortex_documents"
VECTOR_SIZE = 768


client = QdrantClient(url=settings.QDRANT_URL)


def ensure_collection() -> None:
    """Create the Cortex vector collection if it does not already exist."""
    collections = client.get_collections().collections

    if any(collection.name == COLLECTION_NAME for collection in collections):
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


def upsert_chunk(
    *,
    point_id: str,
    workspace_id: int,
    document_id: int,
    chunk_index: int,
    text: str,
    vector: list[float],
) -> None:
    """Store one document chunk with its workspace metadata."""
    if len(vector) != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE}-dimensional vector, got {len(vector)}"
        )

    if not text.strip():
        raise ValueError("Cannot store an empty chunk")

    ensure_collection()

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "workspace_id": workspace_id,
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "text": text,
                },
            )
        ],
    )


def search(
    *,
    workspace_id: int,
    query_vector: list[float],
    limit: int = 5,
) -> list:
    """Search only vectors belonging to the requested workspace."""
    if len(query_vector) != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE}-dimensional query vector, "
            f"got {len(query_vector)}"
        )

    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    ensure_collection()

    workspace_filter = Filter(
        must=[
            FieldCondition(
                key="workspace_id",
                match=MatchValue(value=workspace_id),
            )
        ]
    )

    return client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=workspace_filter,
        limit=limit,
        with_payload=True,
    ).points
