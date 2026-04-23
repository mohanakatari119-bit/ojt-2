import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert import Alert
from app.models.alert_event import AlertEvent
from app.schemas.alert import AlertCreate, AlertOut
from app.schemas.alert_event import AlertEventOut

router = APIRouter(prefix="/v1/alerts", tags=["Alerts"])

VALID_FIELDS = {"status_code", "latency_ms", "error"}
VALID_OPS = {">=", "<=", "==", "!=", ">", "<"}


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db)):
    if body.condition_field not in VALID_FIELDS:
        raise HTTPException(400, f"condition_field must be one of {VALID_FIELDS}")
    if body.condition_operator not in VALID_OPS:
        raise HTTPException(400, f"condition_operator must be one of {VALID_OPS}")

    alert = Alert(**body.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    service_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert)
    if service_id:
        stmt = stmt.where(Alert.service_id == service_id)
    result = await db.execute(stmt.order_by(Alert.created_at.desc()))
    return result.scalars().all()


@router.get("/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
    await db.commit()


@router.get("/{alert_id}/events", response_model=list[AlertEventOut])
async def list_alert_events(
    alert_id: uuid.UUID,
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertEvent)
        .where(AlertEvent.alert_id == alert_id)
        .order_by(AlertEvent.triggered_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/events/recent", response_model=list[AlertEventOut])
async def recent_events(
    service_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(AlertEvent)
        .join(Alert, AlertEvent.alert_id == Alert.id)
        .order_by(AlertEvent.triggered_at.desc())
        .limit(limit)
    )
    if service_id:
        stmt = stmt.where(Alert.service_id == service_id)
    result = await db.execute(stmt)
    return result.scalars().all()
