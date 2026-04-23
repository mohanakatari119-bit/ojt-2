import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models.api_key import APIKey
from app.models.request_log import RequestLog
from app.schemas.request_log import RequestLogIngest, RequestLogOut, RequestLogDetail
from app.schemas.replay import ReplayRequest, ReplayOut
from app.services.alert_engine import evaluate_alerts
from app.services.replay_service import execute_replay
from app.utils.masking import mask_headers

router = APIRouter(prefix="/v1/logs", tags=["Logs"])


@router.post("", response_model=RequestLogOut, status_code=201)
async def ingest_log(
    body: RequestLogIngest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_api_key),
):
    log = RequestLog(
        service_id=api_key.service_id,
        method=body.method.upper(),
        url=body.url,
        path=body.path,
        query_params=body.query_params,
        request_headers=mask_headers(body.request_headers),
        request_body=body.request_body,
        status_code=body.status_code,
        response_headers=mask_headers(body.response_headers),
        response_body=body.response_body,
        latency_ms=body.latency_ms,
        error=body.error,
        source_ip=body.source_ip,
        tags=body.tags,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # Fire-and-forget alert evaluation (errors are swallowed to not block ingestion)
    try:
        await evaluate_alerts(db, log)
    except Exception:
        pass

    return log


@router.get("", response_model=list[RequestLogOut])
async def query_logs(
    service_id: uuid.UUID | None = Query(None),
    method: str | None = Query(None),
    path: str | None = Query(None),
    status_code: int | None = Query(None),
    min_latency_ms: float | None = Query(None),
    max_latency_ms: float | None = Query(None),
    has_error: bool | None = Query(None),
    tag: str | None = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if service_id:
        filters.append(RequestLog.service_id == service_id)
    if method:
        filters.append(RequestLog.method == method.upper())
    if path:
        filters.append(RequestLog.path.ilike(f"%{path}%"))
    if status_code:
        filters.append(RequestLog.status_code == status_code)
    if min_latency_ms is not None:
        filters.append(RequestLog.latency_ms >= min_latency_ms)
    if max_latency_ms is not None:
        filters.append(RequestLog.latency_ms <= max_latency_ms)
    if has_error is True:
        filters.append(RequestLog.error.isnot(None))
    elif has_error is False:
        filters.append(RequestLog.error.is_(None))
    if tag:
        filters.append(RequestLog.tags.contains([tag]))

    stmt = (
        select(RequestLog)
        .where(and_(*filters) if filters else True)
        .order_by(RequestLog.captured_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{log_id}", response_model=RequestLogDetail)
async def get_log(log_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    log = await db.get(RequestLog, log_id)
    if not log:
        raise HTTPException(404, "Log not found")
    return log


@router.post("/{log_id}/replay", response_model=ReplayOut, status_code=201)
async def replay_log(
    log_id: uuid.UUID,
    body: ReplayRequest,
    db: AsyncSession = Depends(get_db),
    api_key: APIKey = Depends(require_api_key),
):
    log = await db.get(RequestLog, log_id)
    if not log:
        raise HTTPException(404, "Log not found")
    if log.service_id != api_key.service_id:
        raise HTTPException(403, "Log belongs to a different service")

    return await execute_replay(db, log, body)
