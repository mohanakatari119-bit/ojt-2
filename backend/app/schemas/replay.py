import uuid
from datetime import datetime
from pydantic import BaseModel


class ReplayRequest(BaseModel):
    override_url: str | None = None
    override_headers: dict | None = None
    override_body: str | None = None


class ReplayOut(BaseModel):
    id: uuid.UUID
    original_log_id: uuid.UUID
    override_url: str | None
    override_headers: dict | None
    override_body: str | None
    status_code: int | None
    response_body: str | None
    response_headers: dict | None
    latency_ms: float | None
    error: str | None
    status: str
    replayed_at: datetime

    model_config = {"from_attributes": True}
