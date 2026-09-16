from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class WorkspaceOut(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberCreate(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    role: Literal["admin", "member"] = "member"


class WorkspaceMemberOut(BaseModel):
    user_id: int
    email: str
    full_name: str | None
    role: Literal["owner", "admin", "member"]
