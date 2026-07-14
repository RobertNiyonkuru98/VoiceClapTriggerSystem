"""Alert workflow + cancellation countdown (FR4.x, NFR2.1, NFR5.2).

The countdown is TICK-DRIVEN (pure): the orchestrator calls `tick()` once per
second. This makes it fully testable and lets the GUI drive it with a QTimer or
the user drive it manually in simulated mode (decision D2).
"""
from __future__ import annotations


class AlertManager:
    def __init__(self, countdown_seconds: int = 10):
        self.countdown_seconds = countdown_seconds
        self.remaining = 0
        self.active = False
        self.cancelled = False
        self.confirmed = False

    def begin(self) -> None:
        self.active = True
        self.cancelled = False
        self.confirmed = False
        self.remaining = self.countdown_seconds

    def tick(self) -> int:
        """Advance one second. Returns remaining seconds (0 when expired)."""
        if not self.active:
            return max(self.remaining, 0)
        self.remaining -= 1
        if self.remaining <= 0:
            self.remaining = 0
            self.active = False
            self.confirmed = True
        return self.remaining

    def cancel(self) -> bool:
        """Cancel during the active window (FR4.4). Returns True if cancelled."""
        if self.active:
            self.active = False
            self.cancelled = True
            return True
        return False

    def is_active(self) -> bool:
        return self.active
