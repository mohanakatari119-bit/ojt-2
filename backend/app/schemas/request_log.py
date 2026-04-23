import uuid
from datetime import datetime
from pydantic import BaseModel


class RequestLogIngest(BaseModel):
    method: str
    url: str
    path: str
    query_params: dict | None = None
    request_headers: dict | None = None
    request_body: str | None = None
    status_code: int | None = None
    response_headers: dict | None = None
    response_body: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    source_ip: str | None = None
    tags: list[str] | None = None


class RequestLogOut(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    method: str
    url: str
    path: str
    status_code: int | None
    latency_ms: float | None
    error: str | None
    tags: list[str] | None
    captured_at: datetime

    model_config = {"from_attributes": True}


class RequestLogDetail(RequestLogOut):
    query_params: dict | None
    request_headers: dict | None
    request_body: str | None
    response_headers: dict | None
    response_body: str | None
    source_ip: str | None


class LogFilter(BaseModel):
    service_id: uuid.UUID | None = None
    method: str | None = None
    path: str | None = None
    status_code: int | None = None
    min_latency_ms: float | None = None
    max_latency_ms: float | None = None
    has_error: bool | None = None
    tag: str | None = None
    limit: int = 50
    offset: int = 0
