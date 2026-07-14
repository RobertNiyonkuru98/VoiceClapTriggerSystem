"""Append-only event logger (FR5.x).

All emergency events are recorded regardless of outcome (NFR5.3 mandatory
logging). Entries are appended as JSON lines so the file is append-only and
cannot be accidentally overwritten at runtime (NFR3.2). A thread-safe lock and
an observer callback let the GUI log viewer update live.
"""
from __future__ import annotations

import json
import threading
from typing import Callable, Optional

from .emergency_event import EmergencyEvent

Observer = Callable[[dict], None]


class EventLogger:
    def __init__(self, path: str = "emergency_events.log"):
        self.path = path
        self._lock = threading.Lock()
        self._observers: list[Observer] = []

    def on_log(self, cb: Observer) -> None:
        self._observers.append(cb)

    def _append(self, entry: dict) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        for cb in self._observers:
            cb(entry)

    # ---- FR5.1 / FR5.2 / FR5.3 / FR5.4 / FR5.5 ----
    def log_keyword(self, phrase: str) -> None:
        self._append({"type": "keyword", "phrase": phrase})

    def log_clap(self, count: int) -> None:
        self._append({"type": "clap", "count": count})

    def log_modifier(self, phrase: Optional[str], category: Optional[str]) -> None:
        self._append({"type": "modifier", "phrase": phrase, "category": category})

    def log_activation(self, event: EmergencyEvent) -> None:
        self._append({"type": "activation", **event.to_dict()})

    def log_cancellation(self, event: EmergencyEvent) -> None:
        self._append({"type": "cancellation", **event.to_dict()})

    def log_error(self, message: str) -> None:
        self._append({"type": "error", "message": message})

    def read_all(self) -> list:
        entries = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
        except FileNotFoundError:
            pass
        return entries
