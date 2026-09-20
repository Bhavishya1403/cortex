from uuid import uuid4

from app.services.document_chunker import chunk_text
from app.services.document_extractor import extract_text
from app.services.embedding_service import embed_text
from app.services.vector_store import upsert_chunk


def ingest_document(
    *,
    document_id: int,
    workspace_id: int,
    file_path: str,
    file_type: str,
) -> int:
    """
    Extract, chunk, embed, and store one document in Qdrant.

    Returns the number of chunks stored.
    """
    text = extract_text(
        file_path=file_path,
        file_type=file_type,
    )

    chunks = chunk_text(text)

    for chunk in chunks:
        vector = embed_text(chunk.text)

        upsert_chunk(
            point_id=str(uuid4()),
            workspace_id=workspace_id,
            document_id=document_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            vector=vector,
        )

    return len(chunks)
