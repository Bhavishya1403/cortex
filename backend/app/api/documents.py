from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.workspaces import get_accessible_workspace
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.document import DocumentOut


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}/documents",
    tags=["documents"],
)

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post(
    "",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    workspace_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    workspace = get_accessible_workspace(workspace_id, db, current_user)

    original_filename = file.filename or "unnamed"
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed types: pdf, txt, md, docx",
        )

    stored_filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_filename

    total_size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File too large. Maximum size is 10 MB",
                    )

                output.write(chunk)
    except HTTPException:
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        )
    finally:
        file.file.close()

    document = Document(
        workspace_id=workspace.id,
        filename=original_filename,
        file_path=str(destination),
        file_type=extension.lstrip("."),
        status="uploaded",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    workspace = get_accessible_workspace(workspace_id, db, current_user)

    return (
        db.query(Document)
        .filter(Document.workspace_id == workspace.id)
        .order_by(Document.id)
        .all()
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    workspace_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    workspace = get_accessible_workspace(workspace_id, db, current_user)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.workspace_id == workspace.id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    workspace_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    workspace = get_accessible_workspace(workspace_id, db, current_user)

    is_owner = workspace.owner_id == current_user.id

    if not is_owner:
        membership = (
            db.query(WorkspaceMember)
            .filter(
                WorkspaceMember.workspace_id == workspace.id,
                WorkspaceMember.user_id == current_user.id,
            )
            .first()
        )
        if membership is None or membership.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the workspace owner or an admin may delete documents",
            )

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.workspace_id == workspace.id,
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.file_path:
        file_path = Path(document.file_path)

        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete the physical file; database record was not modified",
                )

    db.delete(document)
    db.commit()
