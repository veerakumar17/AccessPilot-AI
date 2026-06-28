import uuid
from datetime import datetime

from pydantic import BaseModel, HttpUrl, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    base_url: HttpUrl
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    base_url: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
