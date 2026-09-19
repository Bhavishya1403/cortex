from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    id: int
    workspace_id: int
    filename: str
    file_type: str | None
    status: str
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
