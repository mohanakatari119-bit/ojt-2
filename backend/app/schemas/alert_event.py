import uuid
from datetime import datetime
from pydantic import BaseModel


class AlertEventOut(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    log_id: uuid.UUID
    message: str
    triggered_at: datetime

    model_config = {"from_attributes": True}
