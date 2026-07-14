"""MTEAS — Multi-Trigger Emergency Assistance System.

Modular package implementing the SRS class diagram:
  EmergencySystem (controller) coordinating KeywordDetector, ClapDetector,
  ModifierProcessor, AlertManager, EventLogger, Configuration and EmergencyEvent.

Two driving modes:
  * Live mode  -> real microphone (see EmergencySystem.run_live).
  * Simulated  -> inject events via EmergencySystem.inject_* (tests + GUI).

Heavy deps (speech_recognition, pyaudio, numpy, PyQt6) are imported LAZILY
inside the functions that need them, so the package and its unit tests run with
the standard library only.
"""
from .configuration import ConfigStore, Configuration, DEFAULT_CATEGORIES
from .emergency_event import EmergencyEvent
from .event_logger import EventLogger
from .alert_manager import AlertManager
from .clap_detector import ClapDetector, detect_claps, block_energy
from .keyword_detector import KeywordDetector
from .modifier_processor import ModifierProcessor
from .emergency_system import (
    EmergencySystem,
    STATE_IDLE, STATE_KEYWORD, STATE_CLAP, STATE_MODIFIER, STATE_COUNTDOWN,
)

__all__ = [
    "ConfigStore", "Configuration", "DEFAULT_CATEGORIES",
    "EmergencyEvent", "EventLogger", "AlertManager",
    "ClapDetector", "detect_claps", "block_energy",
    "KeywordDetector", "ModifierProcessor", "EmergencySystem",
    "STATE_IDLE", "STATE_KEYWORD", "STATE_CLAP", "STATE_MODIFIER", "STATE_COUNTDOWN",
]
