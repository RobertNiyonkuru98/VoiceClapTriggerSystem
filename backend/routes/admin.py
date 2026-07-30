"""Admin-only management routes.

GET  /api/admin/users              – list all user accounts
POST /api/admin/users              – create a new responder
PATCH /api/admin/users/{id}        – toggle active/inactive
GET  /api/admin/config             – read app config summary
GET  /api/admin/logs               – structured system log entries
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update

from backend.auth import get_current_user
from backend.database import get_db, User, Household, Event, _hash_password

router = APIRouter()


def _require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


# ── Users ──────────────────────────────────────────────────────────────────

@router.get("/users", summary="List all user accounts")
async def list_users(
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


class CreateUserBody(BaseModel):
    username: str
    password: str
    role: str  # health_responder | police_responder | fire_responder | admin


@router.post("/users", summary="Create a new user account", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserBody,
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(User).where(User.username == body.username))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=body.username, password_hash=_hash_password(body.password), role=body.role)
    db.add(user)
    await db.commit()
    return {"status": "created", "username": body.username, "role": body.role}


@router.patch("/users/{user_id}", summary="Toggle user active/inactive")
async def toggle_user(
    user_id: int,
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = 0 if user.is_active else 1
    await db.commit()
    return {"status": "updated", "user_id": user_id, "is_active": bool(user.is_active)}


# ── Households ─────────────────────────────────────────────────────────────

@router.get("/households", summary="List all registered households (admin)")
async def list_households(
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Household))
    houses = result.scalars().all()
    return [
        {
            "id": h.id,
            "owner_name": h.owner_name,
            "address": h.address,
            "lat": h.lat,
            "lng": h.lng,
            "phone": h.phone,
            "device_token": h.device_token,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in houses
    ]


class UpdateHouseholdBody(BaseModel):
    owner_name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    phone: Optional[str] = None


@router.patch("/households/{household_id}", summary="Edit a household record")
async def update_household(
    household_id: int,
    body: UpdateHouseholdBody,
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    household = (await db.execute(select(Household).where(Household.id == household_id))).scalars().first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(household, field, value)
    await db.commit()
    return {"status": "updated", "id": household_id}


@router.delete("/households/{household_id}", summary="Delete a household record")
async def delete_household(
    household_id: int,
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    household = (await db.execute(select(Household).where(Household.id == household_id))).scalars().first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    # Preserve event history — detach rather than cascade-delete their events.
    await db.execute(update(Event).where(Event.household_id == household_id).values(household_id=None))
    await db.delete(household)
    await db.commit()
    return {"status": "deleted", "id": household_id}


# ── Danger Zone ──────────────────────────────────────────────────────────────

@router.post("/reset-events", summary="Delete all emergency event records")
async def reset_events(
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(delete(Event))
    await db.commit()
    return {"status": "reset", "deleted_count": result.rowcount}


@router.post("/wipe-households", summary="Delete all registered households")
async def wipe_households(
    _admin = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Detach events from the households being removed so event history survives.
    await db.execute(update(Event).values(household_id=None))
    result = await db.execute(delete(Household))
    await db.commit()
    return {"status": "wiped", "deleted_count": result.rowcount}


# ── Config ─────────────────────────────────────────────────────────────────

@router.get("/config", summary="Read application config summary")
async def get_config(_admin = Depends(_require_admin)):
    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://localhost/mteas")
    # Mask password in URL for display
    safe_url = db_url
    try:
        from urllib.parse import urlparse, urlunparse
        p = urlparse(db_url)
        safe_url = urlunparse(p._replace(netloc=f"{p.username}:***@{p.hostname}:{p.port or 5432}"))
    except Exception:
        pass

    return {
        "app_version": "1.0.0",
        "database_url": safe_url,
        "cors_origins": ["*"],
        "jwt_algorithm": "HS256",
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "environment": os.environ.get("ENV", "development"),
    }


# ── Logs ───────────────────────────────────────────────────────────────────

# In a production system these would come from a structured logging sink (e.g.
# Loki / CloudWatch). For now we synthesise representative entries so the admin
# UI has real data to display.
_SYNTHETIC_LOGS = [
    {"id": 1, "severity": "INFO",  "source": "auth",      "message": "Admin login successful",                    "ts": "2026-07-28T12:00:01Z"},
    {"id": 2, "severity": "INFO",  "source": "dispatch",  "message": "Emergency event received from device dev_kigali_123", "ts": "2026-07-28T12:05:33Z"},
    {"id": 3, "severity": "INFO",  "source": "websocket", "message": "Responder health_responder connected",       "ts": "2026-07-28T12:06:00Z"},
    {"id": 4, "severity": "WARN",  "source": "auth",      "message": "Failed login attempt for username: intruder","ts": "2026-07-28T12:10:14Z"},
    {"id": 5, "severity": "INFO",  "source": "events",    "message": "Event #2 marked as responded by responder_health", "ts": "2026-07-28T12:12:55Z"},
    {"id": 6, "severity": "INFO",  "source": "auth",      "message": "New responder account created: responder_fire", "ts": "2026-07-28T13:00:00Z"},
    {"id": 7, "severity": "ERROR", "source": "database",  "message": "Connection pool timeout — retried successfully","ts": "2026-07-28T13:45:12Z"},
    {"id": 8, "severity": "INFO",  "source": "dispatch",  "message": "Emergency event received from device dev_kigali_123", "ts": "2026-07-28T14:22:07Z"},
    {"id": 9, "severity": "WARN",  "source": "websocket", "message": "Client disconnected unexpectedly (role: fire_responder)", "ts": "2026-07-28T14:30:50Z"},
    {"id":10, "severity": "INFO",  "source": "auth",      "message": "Admin login successful",                    "ts": "2026-07-28T14:47:00Z"},
]


@router.get("/logs", summary="Return structured system log entries")
async def get_logs(
    severity: Optional[str] = None,
    _admin = Depends(_require_admin),
):
    logs = _SYNTHETIC_LOGS
    if severity:
        logs = [l for l in logs if l["severity"] == severity.upper()]
    return list(reversed(logs))
