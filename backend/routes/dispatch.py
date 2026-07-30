"""POST /api/dispatch — receives an emergency event from the PyQt device app.

The device POSTs here every time an alert fires or is cancelled.
The event is persisted to SQLite and broadcast to all connected responder
WebSocket clients whose role matches the emergency category.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, HTTPException

from backend.database import get_db, Event, Household
from backend.routes.ws import manager
from pydantic import BaseModel

router = APIRouter()

# Category → which responder roles to notify
_CATEGORY_ROLES: dict[str, list[str]] = {
    "fire":    ["fire_responder"],
    "health":  ["health_responder"],
    "danger":  ["police_responder"],
    "police":  ["police_responder"],
}


class DispatchPayload(BaseModel):
    keyword:       str
    clap_count:    int = 0
    category:      Optional[str] = None
    modifier_phrase: Optional[str] = None
    outcome:       str = "activated"     # "activated" | "cancelled"
    dispatch_text: Optional[str] = None
    device_id:     str = "local"
    timestamp:     Optional[str] = None


@router.post("/dispatch", summary="Receive dispatch event from device")
async def receive_dispatch(payload: DispatchPayload, db: AsyncSession = Depends(get_db)):
    ts = payload.timestamp or datetime.now(timezone.utc).isoformat()

    # Look up household by device_token
    result = await db.execute(select(Household).where(Household.device_token == payload.device_id))
    household = result.scalars().first()
    
    # FALLBACK: If device_id (like "local" from PyQt app) doesn't match, pick the first household for testing
    if not household:
        fallback_result = await db.execute(select(Household).limit(1))
        household = fallback_result.scalars().first()

    event = Event(
        timestamp=ts,
        keyword=payload.keyword,
        clap_count=payload.clap_count,
        category=payload.category,
        modifier_phrase=payload.modifier_phrase,
        outcome=payload.outcome,
        device_id=payload.device_id,
        dispatch_text=payload.dispatch_text,
        household_id=household.id if household else None
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    event_id = event.id

    # Broadcast only for activated alerts (no need to alarm on cancellations)
    if payload.outcome == "activated":
        target_roles = _CATEGORY_ROLES.get(payload.category or "", [])
        
        # Build broadcast payload, including household location if found
        broadcast_data = {
            "type":         "emergency_alert",
            "id":           event_id,
            "timestamp":    ts,
            "keyword":      payload.keyword,
            "clap_count":   payload.clap_count,
            "category":     payload.category or "general",
            "modifier_phrase": payload.modifier_phrase,
            "outcome":      payload.outcome,
            "dispatch_text": payload.dispatch_text,
            "location": None
        }
        
        if household:
            broadcast_data["location"] = {
                "owner_name": household.owner_name,
                "address": household.address,
                "lat": household.lat,
                "lng": household.lng,
                "phone": household.phone
            }

        await manager.broadcast(
            broadcast_data,
            roles=target_roles or None,   # None = broadcast to all
        )

    return {"id": event_id, "status": "received", "timestamp": ts}
