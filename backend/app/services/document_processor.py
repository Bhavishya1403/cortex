from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.document_ingestion import ingest_document


def process_document(
    *,
    document: Document,
    db: Session,
) -> int:
    """
    Process a document and update its lifecycle status.

    Returns the number of chunks ingested.
    """
    document.status = "processing"
    document.error_message = None
    db.commit()
    db.refresh(document)

    try:
        chunk_count = ingest_document(
            document_id=document.id,
            workspace_id=document.workspace_id,
            file_path=document.file_path,
            file_type=document.file_type,
        )

        document.status = "ready"
        document.error_message = None
        db.commit()
        db.refresh(document)

        return chunk_count

    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()
        db.refresh(document)

        raise

