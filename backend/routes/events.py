"""Event log routes — for the Admin and Responder dashboards.

GET   /api/events                    list events (filterable)
GET   /api/events/stats              aggregate counts
PATCH /api/events/{id}/status        acknowledge/resolve an alert
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.auth import get_current_user
from backend.database import get_db, Event, Household
from backend.routes.ws import manager
from backend.routes.dispatch import _CATEGORY_ROLES

router = APIRouter()


@router.get("/events", summary="List emergency events")
async def list_events(
    outcome:  Optional[str] = Query(None, description="Filter by outcome (activated/cancelled)"),
    category: Optional[str] = Query(None, description="Filter by category (fire/health/danger)"),
    limit:    int            = Query(100, le=500, description="Max rows to return"),
    user:     dict           = Depends(get_current_user),
    db:       AsyncSession   = Depends(get_db),
):
    stmt = select(Event, Household).outerjoin(Household, Event.household_id == Household.id)
    if outcome:
        if "," in outcome:
            stmt = stmt.where(Event.outcome.in_(outcome.split(",")))
        else:
            stmt = stmt.where(Event.outcome == outcome)
    if category:
        stmt = stmt.where(Event.category == category)
    stmt = stmt.order_by(Event.timestamp.desc()).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp,
            "keyword": e.keyword,
            "clap_count": e.clap_count,
            "category": e.category,
            "modifier_phrase": e.modifier_phrase,
            "outcome": e.outcome,
            "household_id": e.household_id,
            "device_id": e.device_id,
            "dispatch_text": e.dispatch_text,
            "responder_name": e.responder_name,
            "responded_at": e.responded_at,
            "responder_notes": e.responder_notes,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "location": {
                "lat": h.lat,
                "lng": h.lng,
                "address": h.address,
                "owner_name": h.owner_name,
                "phone": h.phone
            } if h else None
        } for e, h in rows
    ]


@router.get("/events/stats", summary="Aggregate event counts")
async def event_stats(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Event.id)))).scalar() or 0
    activated = (await db.execute(select(func.count(Event.id)).where(Event.outcome == "activated"))).scalar() or 0
    cancelled = (await db.execute(select(func.count(Event.id)).where(Event.outcome == "cancelled"))).scalar() or 0
    responded = (await db.execute(select(func.count(Event.id)).where(Event.responded_at != None))).scalar() or 0
    pending   = max(0, activated - responded)

    # Average trigger-to-acknowledgement latency, in seconds (ties to the SRS
    # hypothesis target of <= 8s response time in 95% of trials).
    rows = (await db.execute(
        select(Event.timestamp, Event.responded_at).where(Event.responded_at != None)
    )).all()

    def _parse(ts: str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None

    deltas = []
    for ts, responded_at in rows:
        t0, t1 = _parse(ts), _parse(responded_at)
        if t0 and t1:
            deltas.append((t1 - t0).total_seconds())
    avg_response_seconds = round(sum(deltas) / len(deltas), 1) if deltas else None

    return {
        "total":     total,
        "activated": activated,
        "cancelled": cancelled,
        "responded": responded,
        "pending":   pending,
        "avg_response_seconds": avg_response_seconds,
    }


@router.patch("/events/{event_id}/status", summary="Update event status")
async def update_event_status(
    event_id: int,
    status_update: dict,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    status = status_update.get("status")
    if status == "acknowledged":
        # Guard against two units acknowledging the same incident at once —
        # this is what makes multi-unit awareness actually enforceable, not
        # just cosmetic in the UI.
        if event.outcome not in ("activated",):
            raise HTTPException(
                status_code=409,
                detail=f"Already {event.outcome} by {event.responder_name or 'another unit'}",
            )
        event.outcome = "acknowledged"
        event.responder_name = status_update.get("responder_name", user["username"])
        event.responded_at = datetime.now(timezone.utc).isoformat()
    elif status == "resolved":
        event.outcome = "resolved"
        notes = status_update.get("notes")
        if notes:
            event.responder_notes = notes

    await db.commit()

    # Broadcast so every other responder of a matching role sees the change
    # live (otherwise only the acknowledging browser's local state updates).
    target_roles = _CATEGORY_ROLES.get(event.category or "", [])
    await manager.broadcast(
        {
            "type": "status_update",
            "id": event.id,
            "outcome": event.outcome,
            "responder_name": event.responder_name,
            "responded_at": event.responded_at,
        },
        roles=target_roles or None,
    )

    return {"status": "updated", "outcome": event.outcome, "responder": event.responder_name}
