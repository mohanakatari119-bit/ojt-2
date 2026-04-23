"""API key authentication dependency."""
import hashlib
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.database import get_db
from app.models.api_key import APIKey
from app.models.service import Service

bearer = HTTPBearer()


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def require_api_key(
    credentials: HTTPAuthorizationCredentials = Security(bearer),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    raw_key = credentials.credentials
    key_hash = _hash_key(raw_key)

    result = await db.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    # Update last_used_at without loading the whole object
    await db.execute(
        update(APIKey)
        .where(APIKey.id == api_key.id)
        .values(last_used_at=func.now())
    )
    await db.commit()
    return api_key
