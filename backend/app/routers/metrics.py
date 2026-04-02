import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.request_log import RequestLog
from app.schemas.metrics import MetricsOut

router = APIRouter(prefix="/v1/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsOut)
async def get_metrics(
    service_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    base_filter = RequestLog.service_id == service_id if service_id else True

    # Totals
    total_q = await db.execute(select(func.count()).select_from(RequestLog).where(base_filter))
    total = total_q.scalar() or 0

    error_q = await db.execute(
        select(func.count()).select_from(RequestLog).where(base_filter, RequestLog.error.isnot(None))
    )
    error_count = error_q.scalar() or 0

    # Latency stats
    latency_q = await db.execute(
        select(
            func.avg(RequestLog.latency_ms),
            func.percentile_cont(0.95).within_group(RequestLog.latency_ms.asc()),
        ).where(base_filter, RequestLog.latency_ms.isnot(None))
    )
    avg_lat, p95_lat = latency_q.one()

    # By method
    method_q = await db.execute(
        select(RequestLog.method, func.count().label("cnt"))
        .where(base_filter)
        .group_by(RequestLog.method)
    )
    by_method = {row.method: row.cnt for row in method_q}

    # By status
    status_q = await db.execute(
        select(RequestLog.status_code, func.count().label("cnt"))
        .where(base_filter, RequestLog.status_code.isnot(None))
        .group_by(RequestLog.status_code)
    )
    by_status = {str(row.status_code): row.cnt for row in status_q}

    # Top paths
    path_q = await db.execute(
        select(RequestLog.path, func.count().label("cnt"))
        .where(base_filter)
        .group_by(RequestLog.path)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_paths = [{"path": row.path, "count": row.cnt} for row in path_q]

    return MetricsOut(
        total_requests=total,
        error_count=error_count,
        error_rate=round(error_count / total, 4) if total else 0.0,
        avg_latency_ms=round(float(avg_lat), 2) if avg_lat is not None else None,
        p95_latency_ms=round(float(p95_lat), 2) if p95_lat is not None else None,
        requests_by_method=by_method,
        requests_by_status=by_status,
        top_paths=top_paths,
    )
