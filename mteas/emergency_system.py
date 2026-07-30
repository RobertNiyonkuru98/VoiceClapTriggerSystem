"""EmergencySystem controller (SRS central controller).

Coordinates KeywordDetector, ClapDetector, ModifierProcessor, AlertManager,
EventLogger and Configuration through the layered-verification state machine:

  IDLE -> KEYWORD -> CLAP_VERIFY -> MODIFIER -> COUNTDOWN -> (ALERT | CANCEL) -> IDLE

Two ways to drive it:
  * Live mode: `run_live()` uses real microphones (Phase C/D wiring).
  * Simulated mode: call `inject_keyword()`, `inject_claps()`,
    `inject_modifier()`, `tick_countdown()`, `cancel()` directly. This is what
    the unit tests and the GUI "simulated mode" use, so the FULL workflow is
    deterministic and demoable without a mic (decision D1, 2026-07-14).
"""
from __future__ import annotations

from typing import Callable, List, Optional

from .alert_manager import AlertManager
from .clap_detector import ClapDetector, block_energy
from .configuration import ConfigStore, Configuration
from .emergency_event import EmergencyEvent
from .event_logger import EventLogger
from .keyword_detector import KeywordDetector
from .modifier_processor import ModifierProcessor

STATE_IDLE = "IDLE"
STATE_KEYWORD = "KEYWORD"
STATE_CLAP = "CLAP_VERIFY"
STATE_MODIFIER = "MODIFIER"
STATE_COUNTDOWN = "COUNTDOWN"

Observer = Callable[[str, dict], None]


class EmergencySystem:
    def __init__(
        self,
        config_store: ConfigStore,
        logger: EventLogger,
        keyword_detector: Optional[KeywordDetector] = None,
        clap_detector: Optional[ClapDetector] = None,
        modifier_processor: Optional[ModifierProcessor] = None,
        alert_manager: Optional[AlertManager] = None,
        dispatch_fn: Optional[callable] = None,
    ):
        self.config_store = config_store
        self.logger = logger
        cfg: Configuration = config_store.current
        self.keyword = keyword_detector or KeywordDetector(cfg.keyword)
        self.clap = clap_detector or ClapDetector(cfg.threshold)
        self.modifier = modifier_processor or ModifierProcessor(cfg.categories)
        self.alert = alert_manager or AlertManager(cfg.countdown_seconds)
        # dispatch_fn(event_dict) -> called on a confirmed alert when a real
        # channel (email/etc.) is configured. None = simulated only (decision D4).
        self.dispatch_fn = dispatch_fn
        self.state = STATE_IDLE
        self._observers: List[Observer] = []
        self._pending_category: Optional[str] = None
        self._pending_claps: int = 0
        self._pending_modifier: Optional[str] = None

    # ---- observer (GUI hook) ----
    def on(self, cb: Observer) -> None:
        self._observers.append(cb)

    def _emit(self, name: str, data: Optional[dict] = None) -> None:
        for cb in self._observers:
            cb(name, data or {})

    @property
    def config(self) -> Configuration:
        return self.config_store.current

    # ---- reset (FR1.5, NFR2.3) ----
    def reset(self) -> None:
        self.state = STATE_IDLE
        self._pending_category = None
        self._pending_claps = 0
        self._pending_modifier = None
        self._emit("state", {"state": self.state})
        self._emit("reset", {})

    # ---- INJECT API (simulated / test / GUI) ----
    def inject_keyword(self, phrase: Optional[str] = None) -> None:
        phrase = (phrase or self.config.keyword).lower()
        self.logger.log_keyword(phrase)
        self.state = STATE_CLAP
        self._emit("keyword", {"phrase": phrase})
        self._emit("state", {"state": self.state})

    def inject_claps(self, count: int) -> None:
        required = self.config.clap_pattern
        self._pending_claps = count
        self.logger.log_clap(count)
        if count >= required:
            self.state = STATE_MODIFIER
            self._emit("clap_ok", {"count": count, "required": required})
            self._emit("state", {"state": self.state})
        else:
            self.logger.log_error(
                f"clap mismatch: got {count}, needed >= {required}"
            )
            self._emit("clap_fail", {"count": count, "required": required})
            self.reset()

    def inject_modifier(self, phrase: Optional[str] = None) -> None:
        category = self.modifier.classify(phrase)
        if category is None:
            # Modifier missed or not spoken -- fall back to a clap-count ->
            # category mapping (household-configurable) instead of always
            # defaulting to "general" (FR3.x resilience: speech recognition
            # of the modifier is the least reliable step in the chain).
            category = self.config.clap_category_map.get(str(self._pending_claps))
        self.logger.log_modifier(phrase, category)
        self._pending_category = category
        self._pending_modifier = phrase
        self.state = STATE_COUNTDOWN
        self.alert.countdown_seconds = self.config.countdown_seconds
        self.alert.begin()
        self._emit("modifier", {"phrase": phrase, "category": category})
        self._emit("countdown_start", {
            "seconds": self.config.countdown_seconds,
            "category": category,
        })
        self._emit("state", {"state": self.state})

    def tick_countdown(self) -> int:
        remaining = self.alert.tick()
        self._emit("countdown_tick", {"remaining": remaining})
        if self.alert.confirmed:
            self._trigger_alert()
        return remaining

    def cancel(self) -> bool:
        if self.alert.is_active():
            self.alert.cancel()
            event = EmergencyEvent(
                keyword=self.config.keyword,
                clap_count=self._pending_claps,
                modifier_phrase=self._pending_modifier,
                category=self._pending_category,
                outcome="cancelled",
            )
            self.logger.log_cancellation(event)
            self._emit("cancelled", {"event": event.to_dict()})
            self.reset()
            return True
        return False

    def _trigger_alert(self) -> None:
        # D4: SIMULATED alert only — never launches/kills real processes.
        event = EmergencyEvent(
            keyword=self.config.keyword,
            clap_count=self._pending_claps,
            modifier_phrase=self._pending_modifier,
            category=self._pending_category,
            outcome="activated",
        )
        self.logger.log_activation(event)
        if self.dispatch_fn is not None:
            try:
                self.dispatch_fn(event.to_dict())
            except Exception as exc:  # NFR5.3: log dispatch failure, keep going
                self.logger.log_error(f"dispatch failed: {exc}")
        self._emit("alert", {"event": event.to_dict()})
        self.reset()

    # ---- LIVE MODE (real microphone) ----
    def run_live(self, tick_sleep: float = 1.0) -> None:
        """Continuous live loop using a real microphone. Blocks; the GUI uses a
        QThread wrapper instead. Provided for the CLI / future wiring."""
        import time
        print(f"[MTEAS] Listening for keyword '{self.config.keyword}'...")
        while True:
            try:
                phrase = self.keyword.listen(self.config.modifier_window_seconds)
                if self.config.keyword in (phrase or ""):
                    self.inject_keyword(phrase)
                    count = self._live_clap_count()
                    self.inject_claps(count)
                    if self.state == STATE_MODIFIER:
                        mod = self.keyword.listen(self.config.modifier_window_seconds)
                        self.inject_modifier(mod)
                    while self.alert.is_active():
                        time.sleep(tick_sleep)
                        self.tick_countdown()
            except Exception as exc:  # NFR5.3: log, then keep running
                self.logger.log_error(str(exc))
                self.reset()

    def _live_clap_count(self) -> int:
        import time
        import numpy as np
        import pyaudio
        cfg = self.config
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1,
                        rate=cfg.mic_sample_rate, input=True,
                        frames_per_buffer=cfg.mic_block_size)
        energies = []
        start = time.time()
        while time.time() - start < cfg.clap_window_seconds:
            data = stream.read(cfg.mic_block_size)
            energies.append(block_energy(data))
        stream.stop_stream()
        stream.close()
        p.terminate()
        count, _ = self.clap.analyze(energies, cfg.mic_block_size / cfg.mic_sample_rate)
        return count
