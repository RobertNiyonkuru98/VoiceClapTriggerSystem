"""Keyword detection (FR1.x).

Two engines, switchable via Configuration.keyword_engine:
  * "google" : SpeechRecognition + Google (needs internet). Simple, already used.
  * "vosk"   : Vosk offline model (no internet) — matches the "always-on device"
               story and removes the network dependency (NFR1). Lazy-imported so
               the dependency is only required when actually selected.

Both share `inject()`/`take_inject()` so the simulated/test path (decision D1)
still works without a microphone or network.
"""
from __future__ import annotations

from typing import Optional


class KeywordDetector:
    def __init__(self, keyword: str = "help", engine: str = "google"):
        self.keyword = keyword
        self.engine = engine
        self._inject: Optional[str] = None

    def inject(self, phrase: Optional[str] = None) -> str:
        """Simulate hearing a phrase (simulated / test mode)."""
        self._inject = phrase if phrase is not None else self.keyword
        return self._inject

    def take_inject(self) -> Optional[str]:
        phrase = self._inject
        self._inject = None
        return phrase

    def listen(self, duration_s: int = 5) -> Optional[str]:
        """Live listen. Delegates to the selected engine."""
        if self.engine == "vosk":
            return self._listen_vosk(duration_s)
        return self._listen_google(duration_s)

    def _listen_google(self, duration_s: int) -> Optional[str]:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=duration_s, phrase_time_limit=duration_s)
        return r.recognize_google(audio).lower()

    def _listen_vosk(self, duration_s: int) -> Optional[str]:
        import wave
        import vosk
        model = vosk.Model("vosk-model-small-en-us-0.15")  # downloaded once
        rec = vosk.KaldiRecognizer(model, 16000)
        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                       input=True, frames_per_buffer=8000)
        stream.start_stream()
        text_parts = []
        import time
        start = time.time()
        while time.time() - start < duration_s:
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                text_parts.append(rec.Result())
        stream.stop_stream(); stream.close(); p.terminate()
        blob = " ".join(text_parts).lower()
        return blob or None
