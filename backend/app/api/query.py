from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.workspaces import get_accessible_workspace
from app.db.session import get_db
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_graph import build_rag_graph


router = APIRouter(
    prefix="/api/workspaces/{workspace_id}",
    tags=["query"],
)


@router.post("/query", response_model=QueryResponse)
def query_workspace(
    workspace_id: int,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    workspace = get_accessible_workspace(
        workspace_id,
        db,
        current_user,
    )

    graph = build_rag_graph()

    result = graph.invoke(
        {
            "workspace_id": workspace.id,
            "query": payload.query,
            "retrieval_limit": payload.retrieval_limit,
        }
    )

    return QueryResponse(
        answer=result["answer"],
        grounded=result.get("grounded", False),
        generation_attempts=result.get("generation_attempts", 0),
    )
