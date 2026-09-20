from app.db.session import SessionLocal
from app.models.document import Document
from app.worker.celery_app import celery_app
from app.services.document_processor import process_document


@celery_app.task
def process_document_task(document_id: int) -> int:
    db = SessionLocal()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()

        if document is None:
            raise ValueError(f"Document {document_id} not found")

        return process_document(document=document, db=db)
    finally:
        db.close()