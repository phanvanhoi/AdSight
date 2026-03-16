from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class BoardCreate(BaseModel):
    name: str
    description: str | None = None


class BoardResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BoardListResponse(BaseModel):
    boards: list[BoardResponse]
