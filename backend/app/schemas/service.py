import uuid
from datetime import datetime
from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    base_url: str | None = None


class ServiceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    base_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
