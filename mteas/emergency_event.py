"""EmergencyEvent — one emergency incident (SRS `EmergencyEvent` class)."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Optional


@dataclass
class EmergencyEvent:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = field(default_factory=time.time)
    keyword: Optional[str] = None
    clap_count: int = 0
    modifier_phrase: Optional[str] = None
    category: Optional[str] = None
    outcome: str = "unknown"   # activated | cancelled | error
    details: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
