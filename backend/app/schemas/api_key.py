import uuid
from datetime import datetime
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    service_id: uuid.UUID


class APIKeyOut(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyOut):
    """Returned once at creation — includes the raw key."""
    raw_key: str
