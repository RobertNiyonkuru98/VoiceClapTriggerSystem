"""Configuration module for MTEAS.

Maps to the SRS `Configuration` class. Holds all tunable settings (keyword,
clap pattern, countdown, categories) and supports saving/loading a profile
store as JSON so settings are NOT hardcoded (FR1.2, FR4.2, NFR3.1).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


# Default emergency categories and the spoken words that map to them (FR3.2).
DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "fire": ["fire", "burning", "smoke", "flame"],
    "health": ["health", "medical", "sick", "hurt", "injured", "help", "emergency"],
    "danger": ["danger", "attack", "violence", "safe", "threat"],
}


@dataclass
class Configuration:
    """A single named profile of settings."""
    keyword: str = "help"
    threshold: int = 700                 # mic energy threshold for a clap onset
    clap_pattern: int = 2                # required claps to confirm intent (FR2.3)
    clap_window_seconds: float = 5.0     # time allowed to clap after keyword (FR2.2)
    modifier_window_seconds: float = 3.0  # time allowed for modifier word (FR3.3)
    countdown_seconds: int = 10          # cancellation window length (FR4.1/FR4.2)
    mic_sample_rate: int = 44100
    mic_block_size: int = 1024
    categories: Dict[str, List[str]] = field(
        default_factory=lambda: dict(DEFAULT_CATEGORIES)
    )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Configuration":
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


class ConfigStore:
    """Manages multiple named profiles + the active one (FR1.2 configurable)."""

    def __init__(self, profiles: Optional[Dict[str, Configuration]] = None,
                 active: str = "default"):
        if profiles is None:
            profiles = {"default": Configuration()}
        self.profiles = profiles
        self.active = active if active in profiles else next(iter(profiles))

    @property
    def current(self) -> Configuration:
        return self.profiles[self.active]

    def set_active(self, name: str) -> None:
        if name not in self.profiles:
            raise KeyError(f"Unknown profile: {name}")
        self.active = name

    def add_profile(self, name: str, config: Optional[Configuration] = None) -> None:
        self.profiles[name] = config or Configuration()

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "profiles": {n: c.to_dict() for n, c in self.profiles.items()},
        }

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ConfigStore":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        profiles = {
            n: Configuration.from_dict(c)
            for n, c in data.get("profiles", {}).items()
        }
        if not profiles:
            profiles = {"default": Configuration()}
        return cls(profiles=profiles, active=data.get("active", "default"))

    @classmethod
    def default(cls) -> "ConfigStore":
        return cls(profiles={"default": Configuration()}, active="default")
