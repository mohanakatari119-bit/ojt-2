from pydantic import BaseModel


class MetricsOut(BaseModel):
    total_requests: int
    error_count: int
    error_rate: float          # 0.0 – 1.0
    avg_latency_ms: float | None
    p95_latency_ms: float | None
    requests_by_method: dict[str, int]
    requests_by_status: dict[str, int]
    top_paths: list[dict]      # [{path, count}]
