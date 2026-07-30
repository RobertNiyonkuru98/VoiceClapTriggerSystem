"""MTEAS Backend API — FastAPI entry point.

Exposes:
  - POST /api/dispatch   — receives emergency events from the PyQt device app
  - WS   /ws/responder   — real-time WebSocket push to responder browsers
  - /api/auth            — JWT login and account registration
  - /api/events          — event log, stats, and status updates
  - /api/admin           — admin-only user and household management
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.dispatch import router as dispatch_router
from backend.routes.events import router as events_router
from backend.routes.auth import router as auth_router
from backend.routes.ws import router as ws_router
from backend.routes.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[MTEAS] Database initialised. Backend ready.")
    yield


app = FastAPI(
    title="MTEAS Backend",
    description=(
        "Multi-Trigger Emergency Assistance System — backend API. "
        "Receives dispatch events from the PyQt device app, persists them in "
        "PostgreSQL, and broadcasts real-time alerts to connected responder browsers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,     prefix="/api/auth",  tags=["Auth"])
app.include_router(dispatch_router, prefix="/api",       tags=["Dispatch"])
app.include_router(events_router,   prefix="/api",       tags=["Events"])
app.include_router(ws_router,                            tags=["WebSocket"])
app.include_router(admin_router,    prefix="/api/admin", tags=["Admin"])


@app.get("/", tags=["Health"])
async def health():
    return {"service": "MTEAS Backend", "version": "1.0.0", "status": "running"}
