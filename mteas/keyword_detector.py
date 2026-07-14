"""Keyword detection (FR1.x).

Live mode uses SpeechRecognition (Google) like the original repo, BUT we also
keep an inject path so tests and the GUI 'simulated mode' can drive the system
without a microphone or network (decision D1 — see docs/DESIGN_DECISIONS.md).
"""
from __future__ import annotations

from typing import Optional


class KeywordDetector:
    def __init__(self, keyword: str = "help"):
        self.keyword = keyword
        self._inject: Optional[str] = None

    def inject(self, phrase: Optional[str] = None) -> str:
        """Simulate hearing a phrase (simulated / test mode)."""
        self._inject = phrase if phrase is not None else self.keyword
        return self._inject

    def take_inject(self) -> Optional[str]:
        """Consume a pending injected phrase, if any."""
        phrase = self._inject
        self._inject = None
        return phrase

    def listen(self, duration_s: int = 5) -> Optional[str]:
        """Live listen via SpeechRecognition (lazy import; needs mic + network)."""
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=duration_s, phrase_time_limit=duration_s)
        return r.recognize_google(audio).lower()
