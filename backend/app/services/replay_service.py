"""Execute an HTTP replay of a stored RequestLog."""
import time
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.replay import Replay
from app.models.request_log import RequestLog
from app.schemas.replay import ReplayRequest


async def execute_replay(db: AsyncSession, log: RequestLog, req: ReplayRequest) -> Replay:
    url = req.override_url or log.url
    headers = {**(log.request_headers or {}), **(req.override_headers or {})}
    body = req.override_body if req.override_body is not None else log.request_body

    replay = Replay(
        original_log_id=log.id,
        override_url=req.override_url,
        override_headers=req.override_headers,
        override_body=req.override_body,
        status="pending",
    )
    db.add(replay)
    await db.flush()

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=log.method,
                url=url,
                headers=headers,
                content=body.encode() if body else None,
            )
        elapsed_ms = (time.monotonic() - start) * 1000

        replay.status_code = response.status_code
        replay.response_body = response.text[:65_536]  # cap at 64 KB
        replay.response_headers = dict(response.headers)
        replay.latency_ms = round(elapsed_ms, 2)
        replay.status = "success"

    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        replay.error = str(exc)
        replay.latency_ms = round(elapsed_ms, 2)
        replay.status = "failed"

    await db.commit()
    await db.refresh(replay)
    return replay
