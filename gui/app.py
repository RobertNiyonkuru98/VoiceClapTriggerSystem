"""PyQt6 GUI for MTEAS (SRS 3.1 — a GUI for non-technical users / responders).

Product mental model (per user, 2026-07-20):
  The device is ALWAYS LISTENING. One click of "Start Listening" powers on the
  session; from then the full trigger runs hands-free from real sound:
      keyword -> clap sequence -> (optional) modifier -> countdown -> dispatch
  The GUI is the RESPONDER CONSOLE: it shows live state, the mic meter, the
  dispatch record, and (during countdown) the CANCEL button. The user does NOT
  click "hear keyword / hear claps" to demo the real flow — those live buttons
  are gone. A collapsed "Developer / Test" panel keeps the inject_* harness for
  deterministic demos without a mic (decision D1).

Live mic work runs in background threads (ListenerThread / CalibrateThread) so
the GUI never blocks and the mic meter updates in real time. There is NO
continuous conflict: only one capture runs at a time.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Optional

from PyQt6.QtCore import pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QSlider, QTextEdit, QListWidget,
    QMessageBox, QGroupBox, QComboBox, QProgressBar, QToolBar, QScrollArea,
    QCheckBox, QDoubleSpinBox,
)

from mteas.configuration import ConfigStore, Configuration
from mteas.emergency_system import EmergencySystem
from mteas.event_logger import EventLogger
from mteas.alert_manager import AlertManager
from mteas.dispatch import build_dispatch, format_dispatch
from mteas.clap_detector import block_energy, detect_claps
from mteas import dispatcher as dispatcher_mod


class Voice:
    """Non-blocking TTS feedback (decision D9). A daemon worker thread
    serializes all speech through one pyttsx3 engine so the GUI thread and
    the ListenerThread are never stalled. Call wait() in a background thread
    when the next step must not start until the prompt has finished."""

    def __init__(self):
        import queue as _queue
        import threading as _threading
        self._engine = None
        self._q = _queue.Queue()
        try:
            import pyttsx3
            e = pyttsx3.init()
            e.setProperty("volume", 1.0)
            e.setProperty("rate", 150)
            self._engine = e
            _threading.Thread(target=self._worker, daemon=True).start()
        except Exception:
            self._engine = None

    def _worker(self) -> None:
        while True:
            text = self._q.get()
            if text is None:
                self._q.task_done()
                return
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass
            self._q.task_done()

    def speak(self, text: str, interrupt: bool = True) -> None:
        """Queue text for TTS. If interrupt=True, flush any stale pending
        utterances so the latest message plays as soon as possible."""
        if self._engine is None:
            return
        if interrupt:
            while not self._q.empty():
                try:
                    self._q.get_nowait()
                    self._q.task_done()
                except Exception:
                    break
        self._q.put(text)

    def wait(self, timeout: float = 15.0) -> None:
        """Block the calling thread until all queued speech has played.
        Safe to call from a background thread (e.g. ListenerThread) to
        ensure a prompt finishes before the next mic capture begins."""
        try:
            self._q.join()
        except Exception:
            import time as _t
            _t.sleep(timeout)


STATE_COLORS = {
    "IDLE": "#2e7d32", "KEYWORD": "#1565c0", "CLAP_VERIFY": "#ef6c00",
    "MODIFIER": "#6a1b9a", "COUNTDOWN": "#c62828",
}


def keyword_recognized(phrase: Optional[str], keyword: str) -> bool:
    return bool(phrase) and keyword in (phrase or "")


class EngineWorker(QThread):
    """Holds the EmergencySystem + logger. Inject API (sim/test) is called from
    the GUI thread; long mic capture is done by background threads."""
    stateChanged = pyqtSignal(str)
    systemEvent = pyqtSignal(str, object)
    logEntry = pyqtSignal(object)

    def __init__(self, config_store: ConfigStore, log_path: str):
        super().__init__()
        self.config_store = config_store
        self.logger = EventLogger(log_path)
        self.logger.on_log(lambda e: self.logEntry.emit(e))
        cfg = config_store.current
        from mteas.keyword_detector import KeywordDetector
        kd = KeywordDetector(cfg.keyword, cfg.keyword_engine)
        self.system = EmergencySystem(config_store, self.logger,
                                      keyword_detector=kd)
        self.system.on(lambda n, d: (self.stateChanged.emit(self.system.state),
                                     self.systemEvent.emit(n, d)))
        self._wire_dispatch()

    def _wire_dispatch(self):
        cfg = self.config_store.current
        if cfg.dispatch_channel == "email" and cfg.responder_email:
            def _send(event_dict):
                from mteas.dispatch import build_dispatch, format_dispatch
                d = build_dispatch(event_dict)
                dispatcher_mod.send_email(cfg.responder_email, format_dispatch(d))
            self.system.dispatch_fn = _send
        else:
            self.system.dispatch_fn = None

    def inject_keyword(self, phrase=None):
        self.system.inject_keyword(phrase)

    def inject_claps(self, count: int):
        self.system.inject_claps(count)

    def inject_modifier(self, phrase=None):
        self.system.inject_modifier(phrase)

    def tick(self):
        if self.system.alert.is_active():
            self.system.tick_countdown()

    def cancel(self):
        self.system.cancel()

    def is_counting_down(self) -> bool:
        return self.system.alert.is_active()

    def calibrate_threshold(self, ambient: list) -> int:
        return self.system.clap.calibrate(ambient)

    def refresh_dispatch(self):
        self._wire_dispatch()


class CalibrateThread(QThread):
    status = pyqtSignal(str)
    done = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, config: Configuration, system: EmergencySystem):
        super().__init__()
        self.config = config
        self.system = system

    def run(self):
        import time
        import pyaudio
        try:
            cfg = self.config
            p = pyaudio.PyAudio()
            st = p.open(format=pyaudio.paInt16, channels=1,
                        rate=cfg.mic_sample_rate, input=True,
                        frames_per_buffer=cfg.mic_block_size)
            ambient = []
            t0 = time.time()
            while time.time() - t0 < 1.0:
                ambient.append(block_energy(st.read(cfg.mic_block_size)))
            st.stop_stream(); st.close(); p.terminate()
            thr = self.system.clap.calibrate(ambient)
            self.done.emit(thr)
            self.status.emit(f"Threshold set to {thr}")
        except Exception as ex:
            self.error.emit(str(ex))


class ListenerThread(QThread):
    """ALWAYS-ON listener (the product's intended behaviour).

    Once started it keeps the mic open in a loop:
      listen keyword -> on match, capture claps -> (optional) modifier ->
      engine drives countdown -> repeat. The GUI feeds off the same engine
    signals, so the responder console updates live with zero clicking.
    """
    micLevel = pyqtSignal(float)
    status = pyqtSignal(str)
    clapProgress = pyqtSignal(str)   # live clap count during capture window
    error = pyqtSignal(str)

    def __init__(self, config: Configuration, system: EmergencySystem, voice: "Voice"):
        super().__init__()
        self.config = config
        self.system = system
        # Shared with DashboardTab (NOT a fresh Voice()) -- two independent
        # pyttsx3 engines speaking on overlapping timelines (step prompts here,
        # countdown/alert narration there) produced garbled/overlapping audio
        # during testing. One engine, one serialized queue, for the whole GUI.
        self.voice = voice
        self._running = False

    def stop_listening(self):
        self._running = False

    def run(self):
        import pyaudio
        try:
            cfg = self.config
            p = pyaudio.PyAudio()
            if cfg.auto_calibrate_on_start:
                # Recalibrate from 1s of room noise. NOTE: this silently
                # overwrites whatever threshold was set in Settings (manually
                # or via the explicit Calibrate button) -- surfacing the
                # resulting number here and letting it be turned off (Settings
                # -> "Auto-calibrate on start") is what makes that visible/
                # controllable instead of the threshold seeming to randomly
                # reset itself every session.
                amb = p.open(format=pyaudio.paInt16, channels=1,
                            rate=cfg.mic_sample_rate, input=True,
                            frames_per_buffer=cfg.mic_block_size)
                ambient = []
                t0 = time.time()
                while time.time() - t0 < 1.0:
                    ambient.append(block_energy(amb.read(cfg.mic_block_size)))
                amb.stop_stream(); amb.close()
                thr = self.system.clap.calibrate(ambient)
                cfg.threshold = thr
                self.status.emit(f"Calibrated threshold: {thr} — Listening always-on (say the keyword)...")
            else:
                # No fresh ambient sample -- but still push the current
                # Settings value into the live detector. Without this, a
                # manually-adjusted-and-saved threshold only takes effect on
                # the next app restart (the detector's threshold is otherwise
                # only ever set at EngineWorker construction or by Calibrate).
                self.system.clap.threshold = cfg.threshold
                self.status.emit(f"Using saved threshold: {cfg.threshold} — Listening always-on (say the keyword)...")
            self._running = True
            stream = p.open(format=pyaudio.paInt16, channels=1,
                            rate=cfg.mic_sample_rate, input=True,
                            frames_per_buffer=cfg.mic_block_size)
            bd = cfg.mic_block_size / cfg.mic_sample_rate
            while self._running:
                # --- keyword window ---
                frames = []
                start = time.time()
                while time.time() - start < cfg.modifier_window_seconds and self._running:
                    data = stream.read(cfg.mic_block_size)
                    e = block_energy(data)
                    frames.append(data)
                    self.micLevel.emit(e)
                phrase = self._recognize(frames, cfg)
                if keyword_recognized(phrase, cfg.keyword):
                    self.status.emit(f"Heard '{phrase}' — clap now")
                    self.voice.speak(f"Keyword heard. Begin the {cfg.clap_pattern} clap sequence.")
                    self.system.inject_keyword(phrase)
                    self.voice.wait()   # let prompt finish before clap window opens
                    # --- clap capture (meter fed live; gate on the required
                    # pattern, matching EmergencySystem's own pass/fail rule --
                    # a partial count like 1-of-2 must fail here too, or this
                    # thread keeps narrating success while the engine has
                    # already silently reset to IDLE via the clap_fail path
                    # below (EngineWorker.system.on(...) -> DashboardTab
                    # already speaks the clap_fail message; don't double it) ---
                    count = self._capture_claps(stream, cfg, bd)
                    if count < cfg.clap_pattern:
                        self.status.emit(
                            f"Only {count}/{cfg.clap_pattern} claps detected — say the keyword and try again."
                        )
                        continue
                    self.voice.speak(f"You clapped {count} times.")
                    self.status.emit(f"Claps: {count} — modifier next (optional)")
                    # --- optional modifier ---
                    if self.system.state == "MODIFIER":
                        self.voice.wait()   # let clap count finish before modifier prompt
                        self.voice.speak("Speak the modifier word now, or stay silent.")
                        self.voice.wait()   # CRITICAL: wait for prompt to FINISH before
                        # opening the capture window — without this, Google Speech sees
                        # the TTS prompt audio instead of the user's voice
                        self._capture_modifier(stream, cfg, bd)
                    # countdown runs on the engine tick (GUI timer drives it)
                # loop continues listening
            stream.stop_stream(); stream.close(); p.terminate()
            self.status.emit("Stopped listening.")
        except Exception as ex:
            self.error.emit(str(ex))

    def _recognize(self, frames, cfg):
        import speech_recognition as sr
        if not frames:
            return ""
        try:
            ad = sr.AudioData(b"".join(frames), cfg.mic_sample_rate, 2)
            return sr.Recognizer().recognize_google(ad).lower()
        except Exception:
            return ""

    def _capture_claps(self, stream, cfg, bd):
        # Brief flush (3 blocks ≈ 70 ms) to clear the TTS echo edge.
        # PyAudio's overflow mechanism already drops frames buffered during
        # voice.wait(), so a long purge is unnecessary and eats clap time.
        for _ in range(3):
            try:
                stream.read(cfg.mic_block_size, exception_on_overflow=False)
            except Exception:
                break
        energies = []
        required = cfg.clap_pattern
        last_count = -1
        start = time.time()
        while time.time() - start < cfg.clap_window_seconds and self._running:
            data = stream.read(cfg.mic_block_size)
            e = block_energy(data)
            energies.append(e)
            self.micLevel.emit(e)
            # Running live count — O(n) on a short list, safe every block
            elapsed = time.time() - start
            remaining = max(0.0, cfg.clap_window_seconds - elapsed)
            current, _ = detect_claps(energies, bd, self.system.clap.threshold)
            if current != last_count:
                last_count = current
                self.clapProgress.emit(
                    f"{current} clap(s) detected — need {required} — "
                    f"{remaining:.0f}s left"
                )
            elif len(energies) % 8 == 0:
                self.status.emit(
                    f"Clap window: {last_count}/{required} claps — {remaining:.0f}s left"
                )
        count, _ = self.system.clap.analyze(energies, bd)
        self.system.inject_claps(count)
        return count

    def _capture_modifier(self, stream, cfg, bd):
        # Flush speaker echo from the modifier prompt (TTS just finished)
        for _ in range(4):
            try:
                stream.read(cfg.mic_block_size, exception_on_overflow=False)
            except Exception:
                break
        frames = []
        start = time.time()
        while time.time() - start < cfg.modifier_window_seconds and self._running:
            frames.append(stream.read(cfg.mic_block_size))
            if len(frames) % 6 == 0:
                remaining = max(0.0, cfg.modifier_window_seconds - (time.time() - start))
                self.status.emit(f"Listening for modifier word… {remaining:.0f}s remaining")
        mod = None
        try:
            import speech_recognition as sr
            mad = sr.AudioData(b"".join(frames), cfg.mic_sample_rate, 2)
            mod = sr.Recognizer().recognize_google(mad).lower()
            self.status.emit(f"Modifier heard: '{mod}'")
            self.voice.speak(f"Modifier received: {mod}.")
        except Exception:
            # Silence or unrecognised — mod stays None (optional per FR 3.1)
            self.status.emit("No modifier heard — proceeding to countdown")
        # Always advance the state machine (CRITICAL: system stays stuck if skipped)
        if self.system.state == "MODIFIER":
            self.system.inject_modifier(mod)


class DashboardTab(QWidget):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        self.worker = worker
        self.listener: Optional[ListenerThread] = None
        lay = QVBoxLayout(self)

        # --- session control (the only "power" button) ---
        self.start_btn = QPushButton("▶ Start Listening")
        self.start_btn.setStyleSheet("background:#1565c0;color:white;font-size:18px;padding:10px;")
        self.start_btn.clicked.connect(self._toggle_listen)
        lay.addWidget(self.start_btn)

        self.state_lbl = QLabel("STATE: IDLE")
        self.state_lbl.setStyleSheet("font-size:22px;font-weight:bold;padding:8px;")
        lay.addWidget(self.state_lbl)

        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 3000)
        self.mic_bar.setValue(0)
        lay.addWidget(QLabel("Mic level (live):"))
        lay.addWidget(self.mic_bar)

        self.status_lbl = QLabel("")
        lay.addWidget(self.status_lbl)

        # countdown + cancel (centered, only meaningful during countdown)
        self.countdown_lbl = QLabel("")
        self.countdown_lbl.setStyleSheet("font-size:48px;color:#c62828;font-weight:bold;")
        self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.countdown_lbl)

        self.cancel_btn = QPushButton("CANCEL EMERGENCY")
        self.cancel_btn.setStyleSheet("background:#c62828;color:white;font-size:20px;padding:14px;")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel)
        lay.addWidget(self.cancel_btn)

        self.last_lbl = QLabel("Last event: —")
        lay.addWidget(self.last_lbl)

        # Developer / Test harness (collapsed; not the product)
        dev = QGroupBox("Developer / Test (simulated, no mic)")
        dev.setCheckable(True); dev.setChecked(False)
        dv = QVBoxLayout(dev)
        self.kw_edit = QLineEdit(worker.config_store.current.keyword)
        b_kw = QPushButton("Inject keyword"); b_kw.clicked.connect(lambda: self.worker.inject_keyword(self.kw_edit.text() or None))
        self.clap_spin = QSpinBox(); self.clap_spin.setRange(0,10); self.clap_spin.setValue(2)
        b_clap = QPushButton("Inject claps"); b_clap.clicked.connect(lambda: self.worker.inject_claps(self.clap_spin.value()))
        self.mod_edit = QLineEdit("i need medical help")
        b_mod = QPushButton("Inject modifier"); b_mod.clicked.connect(lambda: self.worker.inject_modifier(self.mod_edit.text() or None))
        b_auto = QPushButton("Auto-run full flow"); b_auto.clicked.connect(self._auto)
        row = QHBoxLayout(); row.addWidget(QLabel("Keyword:")); row.addWidget(self.kw_edit); row.addWidget(b_kw)
        dv.addLayout(row)
        row2 = QHBoxLayout(); row2.addWidget(QLabel("Claps:")); row2.addWidget(self.clap_spin); row2.addWidget(b_clap)
        dv.addLayout(row2)
        row3 = QHBoxLayout(); row3.addWidget(QLabel("Modifier:")); row3.addWidget(self.mod_edit); row3.addWidget(b_mod)
        dv.addLayout(row3)
        dv.addWidget(b_auto)
        lay.addWidget(dev)

        # Dispatch (IoT-device / responder proxy)
        disp = QGroupBox("Dispatch (responder record)")
        dlay = QVBoxLayout(disp)
        self.dispatch_view = QTextEdit()
        self.dispatch_view.setReadOnly(True)
        self.dispatch_view.setPlainText("No dispatch yet.")
        dlay.addWidget(self.dispatch_view)
        lay.addWidget(disp)

        self.cd_timer = QTimer(); self.cd_timer.setInterval(1000)
        self.cd_timer.timeout.connect(self.worker.tick)
        self.cd_timer.timeout.connect(self._refresh)

        worker.stateChanged.connect(self._on_state)
        worker.systemEvent.connect(self._on_event)
        worker.logEntry.connect(lambda e: None)
        self.voice = Voice()   # persistent TTS for GUI-thread narration

    # ---- session control ----
    def _toggle_listen(self):
        if self.listener and self.listener.isRunning():
            self.listener.stop_listening()
            self.start_btn.setText("▶ Start Listening")
            self.start_btn.setStyleSheet("background:#1565c0;color:white;font-size:18px;padding:10px;")
            return
        self.listener = ListenerThread(self.worker.config_store.current, self.worker.system, self.voice)
        self.listener.micLevel.connect(lambda v: self.mic_bar.setValue(int(min(v, 3000))))
        self.listener.status.connect(self.status_lbl.setText)
        self.listener.clapProgress.connect(self.status_lbl.setText)
        self.listener.error.connect(lambda e: QMessageBox.warning(self, "Listener error", e))
        self.listener.start()
        self.start_btn.setText("■ Stop Listening")
        self.start_btn.setStyleSheet("background:#c62828;color:white;font-size:18px;padding:10px;")

    def _cancel(self):
        self.worker.cancel()

    def _auto(self):
        self.worker.inject_keyword(self.kw_edit.text() or None)
        self.worker.inject_claps(self.clap_spin.value())
        self.worker.inject_modifier(self.mod_edit.text() or None)

    def _on_state(self, state: str):
        self.state_lbl.setText(f"STATE: {state}")
        color = STATE_COLORS.get(state, "#333")
        self.state_lbl.setStyleSheet(f"font-size:22px;font-weight:bold;padding:8px;color:{color};")
        if state == "COUNTDOWN":
            self.cancel_btn.setEnabled(True)
            self.cd_timer.start()
        else:
            self.cd_timer.stop()
            self.cancel_btn.setEnabled(False)
            if state == "IDLE":
                self.countdown_lbl.setText("")

    def _on_event(self, name: str, data):
        if name == "countdown_tick":
            remaining = data.get('remaining', 0)
            self.countdown_lbl.setText(f"{remaining}s")
            # Speak key countdown moments so the user can hear the timer
            if remaining in (5, 3, 2, 1):
                self.voice.speak(str(remaining))
        elif name == "countdown_start":
            seconds = data.get('seconds', 0)
            cat = data.get('category') or 'general'
            self.countdown_lbl.setText(f"{seconds}s")
            self.voice.speak(
                f"Emergency alert in {seconds} seconds. "
                f"Category: {cat}. Press cancel to abort."
            )
        elif name == "alert":
            self.countdown_lbl.setText("ALERT SENT")
            event = data.get("event", {})
            cfg = self.worker.config_store.current
            d = build_dispatch(event, channel=cfg.dispatch_channel)
            dispatch_text = format_dispatch(d)
            self.dispatch_view.setPlainText(dispatch_text)
            self.last_lbl.setText(f"Last event: ALERT ({event.get('category')})")
            self.voice.speak("Emergency triggered. Help is on the way.")
            # POST to backend if configured (non-blocking daemon thread)
            if cfg.dispatch_channel == "backend":
                self._post_to_backend(cfg.backend_url, {
                    "keyword":      event.get("keyword", ""),
                    "clap_count":   event.get("clap_count", 0),
                    "category":     event.get("category"),
                    "modifier_phrase": event.get("modifier_phrase"),
                    "outcome":      "activated",
                    "dispatch_text": dispatch_text,
                    "device_id":    cfg.device_token or "local",
                })
            QMessageBox.warning(self, "Emergency Alert", dispatch_text)
        elif name == "cancelled":
            self.countdown_lbl.setText("CANCELLED")
            self.dispatch_view.setPlainText("DISPATCH CANCELLED - no alert sent.")
            self.last_lbl.setText("Last event: CANCELLED")
            self.voice.speak("Emergency cancelled.")
            event = data.get("event", {})
            cfg = self.worker.config_store.current
            if cfg.dispatch_channel == "backend":
                self._post_to_backend(cfg.backend_url, {
                    "keyword":      event.get("keyword", ""),
                    "clap_count":   event.get("clap_count", 0),
                    "category":     event.get("category"),
                    "modifier_phrase": event.get("modifier_phrase"),
                    "outcome":      "cancelled",
                    "device_id":    cfg.device_token or "local",
                })
        elif name == "clap_fail":
            count = data.get('count', 0)
            required = data.get('required', 2)
            msg = f"Detected {count}/{required} claps — resetting"
            self.last_lbl.setText(f"Last event: {msg}")
            self.status_lbl.setText(f"⚠️ {msg}. Say the keyword and try again.")
            self.voice.speak(
                f"Detected {count} clap{'s' if count != 1 else ''}. "
                f"Need {required}. Please say the keyword and try again."
            )
        elif name == "reset":
            self.mic_bar.setValue(0)

    def _refresh(self):
        if self.worker.is_counting_down():
            self.countdown_lbl.setText(f"{self.worker.system.alert.remaining}s")
        else:
            self.cd_timer.stop()
            self.cancel_btn.setEnabled(False)

    def _post_to_backend(self, url: str, payload: dict):
        import threading
        def _send():
            try:
                cfg = self.worker.config_store.current
                token = getattr(cfg, "device_token", "")
                import requests
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                requests.post(f"{url.rstrip('/')}/api/dispatch", json=payload, headers=headers, timeout=5)
            except Exception:
                pass
        threading.Thread(target=_send, daemon=True).start()


class SettingsTab(QWidget):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        self.worker = worker
        cs = worker.config_store
        cfg = cs.current

        # Wrap in a scroll area so nothing is clipped on small screens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        inner = QWidget()
        scroll.setWidget(inner)
        lay = QVBoxLayout(inner)

        # ── How it works ───────────────────────────────────────────────
        flow_box = QGroupBox("⚡ How MTEAS works")
        fl = QVBoxLayout(flow_box)
        flow_lbl = QLabel(
            "① Say the <b>emergency keyword</b> (e.g. \"jesus\")<br>"
            "② <b>Clap</b> the required number of times within the window<br>"
            "③ (Optional) Speak a <b>modifier word</b> to name the emergency type<br>"
            "④ A countdown starts — press <b>CANCEL</b> to abort<br>"
            "⑤ If not cancelled, the alert is dispatched"
        )
        flow_lbl.setWordWrap(True)
        flow_lbl.setStyleSheet("color:#444;padding:4px;line-height:1.8;")
        fl.addWidget(flow_lbl)
        lay.addWidget(flow_box)

        # ── Core settings ──────────────────────────────────────────
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(cs.profiles.keys()))
        self.profile_combo.setCurrentText(cs.active)
        self.profile_combo.currentTextChanged.connect(self._load_profile)
        lay.addWidget(QLabel("Active profile:")); lay.addWidget(self.profile_combo)

        self.kw = QLineEdit(cfg.keyword)
        self.kw.setToolTip("The word you say to start the emergency flow (e.g. 'jesus')")

        self.thr = QSlider(Qt.Orientation.Horizontal); self.thr.setRange(100, 3000)
        self.thr.setValue(cfg.threshold)
        self.thr.setToolTip(
            "Mic energy level a sound must reach to count as a clap.\n"
            "Use the Calibrate button to set this automatically from room noise."
        )

        self.pat = QSpinBox(); self.pat.setRange(1, 10); self.pat.setValue(cfg.clap_pattern)
        self.pat.setToolTip(
            "How many claps must be heard after the keyword.\n"
            "e.g. 2 means you must clap exactly twice."
        )

        self.cd = QSpinBox(); self.cd.setRange(1, 60); self.cd.setValue(cfg.countdown_seconds)
        self.cd.setToolTip("Seconds before the alert fires — press CANCEL during this window to abort")

        self.clap_win = QDoubleSpinBox(); self.clap_win.setRange(1.0, 15.0); self.clap_win.setSingleStep(0.5)
        self.clap_win.setValue(cfg.clap_window_seconds)
        self.clap_win.setToolTip("How many seconds you have to clap after the keyword is heard")

        self.mod_win = QDoubleSpinBox(); self.mod_win.setRange(1.0, 15.0); self.mod_win.setSingleStep(0.5)
        self.mod_win.setValue(cfg.modifier_window_seconds)
        self.mod_win.setToolTip(
            "How many seconds you have to speak the modifier word after clapping.\n"
            "Increase this if the modifier keeps failing to be recognised."
        )

        self.engine = QComboBox(); self.engine.addItems(["google", "vosk"])
        self.engine.setCurrentText(cfg.keyword_engine)
        self.engine.setToolTip(
            "google = online (needs internet, more accurate)\n"
            "vosk   = offline (works without internet)"
        )

        self.channel = QComboBox(); self.channel.addItems(["simulated", "email", "backend"])
        self.channel.setCurrentText(cfg.dispatch_channel)
        self.responder = QLineEdit(cfg.responder_email)
        self.responder.setPlaceholderText("e.g. responder@example.com")
        self.backend_url = QLineEdit(getattr(cfg, "backend_url", "http://localhost:8000"))
        self.backend_url.setPlaceholderText("http://localhost:8000")
        
        self.device_token = QLineEdit(getattr(cfg, "device_token", ""))
        self.device_token.setPlaceholderText("Token generated by Admin Portal")

        for w, lbl in [
            (self.kw,          "Emergency keyword:"),
            (self.thr,         "Clap threshold (auto-set by Calibrate):"),
            (self.pat,         "Required claps:"),
            (self.clap_win,    "Clap capture window (seconds):"),
            (self.mod_win,     "Modifier capture window (seconds):"),
            (self.cd,          "Countdown seconds:"),
            (self.engine,      "Keyword engine (google = online, vosk = offline):"),
            (self.channel,     "Dispatch channel:"),
            (self.responder,   "Responder email (for email dispatch):"),
            (self.backend_url, "Backend API URL (for backend dispatch):"),
            (self.device_token,"Device Token (links to Household):"),
        ]:
            lay.addWidget(QLabel(lbl)); lay.addWidget(w)

        self.b_cal = QPushButton("🎤  Calibrate clap threshold from room noise")
        self.b_cal.setToolTip(
            "Records 1 second of ambient noise and sets the clap threshold\n"
            "automatically. Run this before each session for best results."
        )
        self.b_cal.clicked.connect(self._calibrate)
        lay.addWidget(self.b_cal)

        self.auto_cal = QCheckBox("Auto-calibrate threshold every time Start Listening is pressed")
        self.auto_cal.setChecked(cfg.auto_calibrate_on_start)
        self.auto_cal.setToolTip(
            "On: the threshold is recalculated from 1s of room noise on every\n"
            "\"Start Listening\" click, silently overriding whatever is set above.\n"
            "Off: the threshold value shown above is used as-is, unchanged."
        )
        lay.addWidget(self.auto_cal)

        btn = QPushButton("💾  Save profile")
        btn.clicked.connect(self._save)
        lay.addWidget(btn)
        self.status = QLabel(""); lay.addWidget(self.status)

        # ── Editable emergency categories ────────────────────────────
        cat_box = QGroupBox("🏷  Emergency Categories (modifier words)")
        cat_lay = QVBoxLayout(cat_box)
        cat_help = QLabel(
            "After clapping, say a word from one of these categories to label "
            "the emergency type. Edit the comma-separated keywords and Save."
        )
        cat_help.setWordWrap(True)
        cat_help.setStyleSheet("color:#666;font-size:11px;padding-bottom:6px;")
        cat_lay.addWidget(cat_help)
        self._cat_edits: Dict[str, QLineEdit] = {}
        for cat, keywords in cfg.categories.items():
            row = QHBoxLayout()
            lbl = QLabel(f"{cat.capitalize()}:")
            lbl.setFixedWidth(72)
            lbl.setStyleSheet("font-weight:bold;")
            edit = QLineEdit(", ".join(keywords))
            edit.setToolTip(
                f"Comma-separated words that classify the emergency as '{cat}'.\n"
                "Example for fire: fire, smoke, burning, flame"
            )
            self._cat_edits[cat] = edit
            row.addWidget(lbl)
            row.addWidget(edit)
            cat_lay.addLayout(row)
        lay.addWidget(cat_box)

        # ── Clap-count -> category fallback ──────────────────────────
        clap_cat_box = QGroupBox("👏 Clap Count → Category (fallback when no modifier is heard)")
        ccc_lay = QVBoxLayout(clap_cat_box)
        ccc_help = QLabel(
            "If the modifier word isn't recognised (or none is spoken), the category "
            "is looked up here by how many times you clapped, instead of always "
            "falling back to 'general'. Leave a row as '(none)' to skip it."
        )
        ccc_help.setWordWrap(True)
        ccc_help.setStyleSheet("color:#666;font-size:11px;padding-bottom:6px;")
        ccc_lay.addWidget(ccc_help)
        self._clap_cat_combos: Dict[int, QComboBox] = {}
        clap_cat_options = ["(none)"] + sorted(cfg.categories.keys()) + ["general"]
        for count in range(1, 6):
            row = QHBoxLayout()
            lbl = QLabel(f"{count} clap{'s' if count != 1 else ''}:")
            lbl.setFixedWidth(72)
            combo = QComboBox(); combo.addItems(clap_cat_options)
            current = cfg.clap_category_map.get(str(count), "")
            combo.setCurrentText(current if current in clap_cat_options else "(none)")
            self._clap_cat_combos[count] = combo
            row.addWidget(lbl)
            row.addWidget(combo)
            ccc_lay.addLayout(row)
        lay.addWidget(clap_cat_box)

    def _load_profile(self, name):
        self.worker.config_store.set_active(name)
        cfg = self.worker.config_store.current
        self.kw.setText(cfg.keyword); self.thr.setValue(cfg.threshold)
        self.pat.setValue(cfg.clap_pattern); self.cd.setValue(cfg.countdown_seconds)
        self.clap_win.setValue(cfg.clap_window_seconds)
        self.mod_win.setValue(cfg.modifier_window_seconds)
        self.auto_cal.setChecked(cfg.auto_calibrate_on_start)
        self.engine.setCurrentText(cfg.keyword_engine)
        self.channel.setCurrentText(cfg.dispatch_channel)
        self.responder.setText(cfg.responder_email)
        self.backend_url.setText(getattr(cfg, "backend_url", "http://localhost:8000"))
        self.device_token.setText(getattr(cfg, "device_token", ""))
        for cat, edit in self._cat_edits.items():
            edit.setText(", ".join(cfg.categories.get(cat, [])))
        for count, combo in self._clap_cat_combos.items():
            current = cfg.clap_category_map.get(str(count), "")
            options = [combo.itemText(i) for i in range(combo.count())]
            combo.setCurrentText(current if current in options else "(none)")

    def _calibrate(self):
        self.b_cal.setEnabled(False)
        self.cal_thread = CalibrateThread(self.worker.config_store.current, self.worker.system)
        self.cal_thread.status.connect(self.status.setText)
        self.cal_thread.done.connect(lambda thr: (setattr(self.worker.config_store.current, "threshold", thr),
                                                  self.thr.setValue(thr),
                                                  self.status.setText(f"✅ Threshold set to {thr}")))
        self.cal_thread.error.connect(lambda e: QMessageBox.warning(self, "Calibrate error", e))
        self.cal_thread.finished.connect(lambda: self.b_cal.setEnabled(True))
        self.cal_thread.start()

    def _save(self):
        cfg = self.worker.config_store.current
        cfg.keyword = self.kw.text().strip() or cfg.keyword
        cfg.threshold = self.thr.value()
        cfg.clap_pattern = self.pat.value()
        cfg.clap_window_seconds = self.clap_win.value()
        cfg.modifier_window_seconds = self.mod_win.value()
        cfg.countdown_seconds = self.cd.value()
        cfg.auto_calibrate_on_start = self.auto_cal.isChecked()
        cfg.keyword_engine = self.engine.currentText()
        cfg.dispatch_channel = self.channel.currentText()
        cfg.responder_email = self.responder.text().strip()
        cfg.backend_url = self.backend_url.text().strip() or "http://localhost:8000"
        cfg.device_token = self.device_token.text().strip()
        # Also push the threshold live immediately -- otherwise it only takes
        # effect on the next app restart (the detector reads it once at
        # construction) or the next auto-calibration.
        self.worker.system.clap.threshold = cfg.threshold
        # Parse editable category QLineEdits back into lists
        for cat, edit in self._cat_edits.items():
            keywords = [kw.strip().lower() for kw in edit.text().split(",") if kw.strip()]
            if keywords:
                cfg.categories[cat] = keywords
        cfg.clap_category_map = {
            str(count): combo.currentText()
            for count, combo in self._clap_cat_combos.items()
            if combo.currentText() != "(none)"
        }
        store = self.worker.config_store
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mteas_config.json")
        store.save(path)
        self.worker.refresh_dispatch()
        self.status.setText(f"✅ Saved profile '{store.active}'")


class LogTab(QWidget):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        lay = QVBoxLayout(self)
        self.list = QListWidget()
        lay.addWidget(self.list)
        worker.logEntry.connect(self._append)

    def _append(self, entry: Dict):
        self.list.addItem(f"{entry.get('type'):<12} {entry}")


class MainWindow(QMainWindow):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        self.setWindowTitle("MTEAS — Multi-Trigger Emergency Assistance System")
        self.resize(760, 680)
        self.worker = worker
        tabs = QTabWidget()
        tabs.addTab(DashboardTab(worker), "Dashboard")
        tabs.addTab(SettingsTab(worker), "Settings")
        tabs.addTab(LogTab(worker), "Event Log")
        self.setCentralWidget(tabs)

    def closeEvent(self, event):
        self.worker.cancel()
        event.accept()


def main():
    app = QApplication(sys.argv)
    base = os.path.dirname(os.path.dirname(__file__))
    cfg_path = os.path.join(base, "mteas_config.json")
    if os.path.exists(cfg_path):
        try:
            store = ConfigStore.load(cfg_path)
        except Exception:
            store = ConfigStore.default()
    else:
        # First run: seed with the original project's settings so the keyword
        # the user trained on ("jesus") carries over (config.py WAKE_WORD).
        store = ConfigStore.default()
        store.current.keyword = "jesus"
        store.current.threshold = 500
        store.save(cfg_path)
    log_path = os.path.join(base, "emergency_events.log")
    worker = EngineWorker(store, log_path)
    win = MainWindow(worker)
    win.show()
    rc = app.exec()
    sys.exit(rc)


if __name__ == "__main__":
    main()
