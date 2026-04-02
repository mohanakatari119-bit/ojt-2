import hashlib
import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.service import Service
from app.models.api_key import APIKey
from app.schemas.service import ServiceCreate, ServiceOut
from app.schemas.api_key import APIKeyCreate, APIKeyOut, APIKeyCreated

router = APIRouter(prefix="/v1/services", tags=["Services"])


@router.post("", response_model=ServiceOut, status_code=201)
async def create_service(body: ServiceCreate, db: AsyncSession = Depends(get_db)):
    service = Service(**body.model_dump())
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("", response_model=list[ServiceOut])
async def list_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).order_by(Service.created_at.desc()))
    return result.scalars().all()


@router.get("/{service_id}", response_model=ServiceOut)
async def get_service(service_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    svc = await db.get(Service, service_id)
    if not svc:
        raise HTTPException(404, "Service not found")
    return svc


# ── API Keys ──────────────────────────────────────────────────────────────────

@router.post("/{service_id}/keys", response_model=APIKeyCreated, status_code=201)
async def create_api_key(service_id: uuid.UUID, body: APIKeyCreate, db: AsyncSession = Depends(get_db)):
    svc = await db.get(Service, service_id)
    if not svc:
        raise HTTPException(404, "Service not found")

    raw_key = f"mkey_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    api_key = APIKey(
        service_id=service_id,
        name=body.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return APIKeyCreated(
        id=api_key.id,
        service_id=api_key.service_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        raw_key=raw_key,
    )


@router.get("/{service_id}/keys", response_model=list[APIKeyOut])
async def list_api_keys(service_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(APIKey).where(APIKey.service_id == service_id).order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()
