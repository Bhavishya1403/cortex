from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    retrieval_limit: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    grounded: bool
    generation_attempts: int
