"""Dispatch record builder — the IoT-device proxy output (FR6 FUTURE proxy).

The real IoT device + responder backend do not exist in the prototype, so this
module produces the DISPATCH record the device WOULD broadcast. It is pure and
unit-testable (no PyQt / no hardware).
"""
from __future__ import annotations

from typing import Dict
from .emergency_event import EmergencyEvent


def build_dispatch(event, recipient: str = "Emergency Responder",
                   channel: str = "simulated") -> Dict:
    """Build the dispatch record for an emergency event.

    `event` may be an EmergencyEvent or a plain dict (e.g. an observer payload).
    `channel` is the dispatch channel name ("simulated", "email", "sms", ...).
    A "simulated" channel stays SIMULATED; any real channel is marked SENT.
    """
    if not isinstance(event, EmergencyEvent):
        fields = EmergencyEvent.__dataclass_fields__
        event = EmergencyEvent(
            **{k: v for k, v in (event or {}).items() if k in fields}
        )
    cat = event.category or "unspecified"
    is_sim = (channel or "simulated").lower() == "simulated"
    return {
        "event_id": event.event_id,
        "recipient": recipient,
        "category": cat,
        "channel": channel,
        "status": "SIMULATED" if is_sim else "SENT",
        "timestamp": event.timestamp,
        "modifier_phrase": event.modifier_phrase,
    }


def format_dispatch(d: Dict) -> str:
    modifier_line = (
        f"  Modifier: \"{d['modifier_phrase']}\"\n" if d.get("modifier_phrase") else ""
    )
    return (
        "DISPATCH SENT\n"
        f"  To      : {d['recipient']}\n"
        f"  Category: {d['category']} emergency\n"
        f"{modifier_line}"
        f"  Channel : {d['channel']}\n"
        f"  Event   : {d['event_id']}\n"
        f"  Status  : {d['status']}\n"
        "  (IoT-device proxy - no real hardware connected)"
    )
