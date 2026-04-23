from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import pathlib

from app.database import engine, Base
from app.models import *  # noqa: F401 — register all models
from app.routers import services, logs, metrics, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="API Monitor",
    version="1.0.0",
    description="Developer-first API monitoring & debugging system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(services.router)
app.include_router(logs.router)
app.include_router(metrics.router)
app.include_router(alerts.router)


# ── Serve the UI ──────────────────────────────────────────────────────────────
STATIC_DIR = pathlib.Path(
    os.environ.get("FRONTEND_DIR", str(pathlib.Path(__file__).parent.parent.parent / "frontend"))
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR / "static")), name="static")

    @app.get("/", include_in_schema=False)
    async def ui_root():
        return FileResponse(str(STATIC_DIR / "index.html"))

    @app.get("/dashboard", include_in_schema=False)
    async def ui_dashboard():
        return FileResponse(str(STATIC_DIR / "dashboard.html"))

    @app.get("/log/{log_id}", include_in_schema=False)
    async def ui_log_detail(log_id: str):
        return FileResponse(str(STATIC_DIR / "log-detail.html"))

    @app.get("/replay/{log_id}", include_in_schema=False)
    async def ui_replay(log_id: str):
        return FileResponse(str(STATIC_DIR / "replay.html"))

    @app.get("/metrics-ui", include_in_schema=False)
    async def ui_metrics():
        return FileResponse(str(STATIC_DIR / "metrics.html"))

    @app.get("/alerts-ui", include_in_schema=False)
    async def ui_alerts():
        return FileResponse(str(STATIC_DIR / "alerts.html"))


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
