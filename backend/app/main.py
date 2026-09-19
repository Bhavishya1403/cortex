from fastapi import Depends, FastAPI

from app.api.auth import router as auth_router
from app.api.deps import get_current_user
from app.api.documents import router as documents_router
from app.api.workspaces import router as workspaces_router
from app.models.user import User


app = FastAPI(title="Cortex API")

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(documents_router)


@app.get("/health")
def health_check() -> dict:
    """Minimal liveness check."""
    return {"status": "ok"}


@app.get("/api/me")
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
