import uuid
from datetime import datetime
from pydantic import BaseModel


class AlertCreate(BaseModel):
    service_id: uuid.UUID
    name: str
    description: str | None = None
    condition_field: str      # status_code | latency_ms | error
    condition_operator: str   # >= <= == != > <
    condition_value: str
    is_active: bool = True


class AlertOut(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    name: str
    description: str | None
    condition_field: str
    condition_operator: str
    condition_value: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
