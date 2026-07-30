"""WebSocket hub — real-time alert broadcast to responder browsers.

Responders connect to /ws/responder?role=<their_role>.
When a dispatch event arrives (via POST /api/dispatch), the dispatch route
calls `manager.broadcast()` which pushes JSON to every connected client
whose role matches the emergency category.
"""
from __future__ import annotations

import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class _ConnectionManager:
    def __init__(self):
        # role -> set of live WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, role: str) -> None:
        await ws.accept()
        self._connections.setdefault(role, set()).add(ws)
        print(f"[WS] +1 connection  role={role!r}  "
              f"total={sum(len(v) for v in self._connections.values())}")

    def disconnect(self, ws: WebSocket, role: str) -> None:
        self._connections.get(role, set()).discard(ws)
        print(f"[WS] -1 connection  role={role!r}  "
              f"total={sum(len(v) for v in self._connections.values())}")

    async def broadcast(self, message: dict, roles: list[str] | None = None) -> None:
        """Send `message` to all connections, or only to `roles` if given."""
        text = json.dumps(message, default=str)
        if roles is None:
            targets = {ws for conns in self._connections.values() for ws in conns}
        else:
            targets = {ws for r in roles for ws in self._connections.get(r, set())}
            # always include 'all' subscribers
            targets |= self._connections.get("all", set())

        dead: list[WebSocket] = []
        for ws in list(targets):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)

        for ws in dead:
            for conns in self._connections.values():
                conns.discard(ws)


# Singleton shared by dispatch route + WebSocket endpoint
manager = _ConnectionManager()


@router.websocket("/ws/responder")
async def responder_websocket(ws: WebSocket, role: str = "all"):
    """
    Connect with ?role=fire_responder|health_responder|police_responder|all|admin.
    The server sends JSON messages of type 'emergency_alert' or 'ping'.
    Clients send any text to keep the connection alive.
    """
    await manager.connect(ws, role)
    try:
        while True:
            await ws.receive_text()   # keep alive; client sends periodic pings
    except WebSocketDisconnect:
        manager.disconnect(ws, role)
