"""PyQt6 GUI for MTEAS (SRS 3.1 endorses a GUI for non-technical users).

Layout (three tabs):
  * Dashboard : current state, last event, LIVE countdown + CANCEL button,
                a mic-level meter, a real "Capture" flow (real mic), and a
                Simulated-controls panel (inject keyword / claps / modifier /
                tick / cancel) so the whole SRS workflow is demoable
                deterministically without a mic.
  * Settings  : keyword, threshold, clap pattern, countdown, manage profiles
                (FR1.2, FR4.2, NFR3.1).
  * Event Log : live, append-only view of every logged event (FR5.x, NFR3.2).

Live mic work runs in `LiveCaptureThread` (a QThread) so the GUI never blocks
and the mic meter updates in real time. There is NO continuous background mic
loop and NO mode toggle — capture happens only when you press a real-capture
button, so the mic is never held by two consumers at once.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional

from PyQt6.QtCore import pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QSlider, QTextEdit, QListWidget,
    QMessageBox, QGroupBox, QComboBox, QProgressBar, QToolBar,
)

from mteas.configuration import ConfigStore, Configuration
from mteas.emergency_system import EmergencySystem
from mteas.event_logger import EventLogger
from mteas.alert_manager import AlertManager
from mteas.dispatch import build_dispatch, format_dispatch
from mteas.clap_detector import block_energy


STATE_COLORS = {
    "IDLE": "#2e7d32", "KEYWORD": "#1565c0", "CLAP_VERIFY": "#ef6c00",
    "MODIFIER": "#6a1b9a", "COUNTDOWN": "#c62828",
}


def keyword_recognized(phrase: Optional[str], keyword: str) -> bool:
    """True only if the heard phrase actually contains the emergency keyword."""
    return bool(phrase) and keyword in (phrase or "")


class EngineWorker(QThread):
    """Holds the EmergencySystem + logger. Inject API is called from the GUI
    thread (fast, pure Python); long mic capture is done by LiveCaptureThread."""
    stateChanged = pyqtSignal(str)
    systemEvent = pyqtSignal(str, object)
    logEntry = pyqtSignal(object)

    def __init__(self, config_store: ConfigStore, log_path: str):
        super().__init__()
        self.config_store = config_store
        self.logger = EventLogger(log_path)
        self.logger.on_log(lambda e: self.logEntry.emit(e))
        self.system = EmergencySystem(config_store, self.logger)
        self.system.on(lambda n, d: (self.stateChanged.emit(self.system.state),
                                     self.systemEvent.emit(n, d)))

    # --- simulated / test API (called from GUI thread) ---
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


class LiveCaptureThread(QThread):
    """Real-microphone capture, off the GUI thread.

    mode='keyword': records `modifier_window_seconds`, feeds the meter live,
                    then runs SpeechRecognition (Google) and emits the phrase.
    mode='claps'  : records `clap_window_seconds`, feeds the meter live, then
                    runs the clap detector and emits the clap count.
    """
    micLevel = pyqtSignal(float)
    status = pyqtSignal(str)
    done = pyqtSignal(str, object)   # (mode, value)
    error = pyqtSignal(str)

    def __init__(self, mode: str, config: Configuration, system: EmergencySystem):
        super().__init__()
        self.mode = mode
        self.config = config
        self.system = system

    def run(self):
        import time
        import pyaudio
        import speech_recognition as sr
        try:
            cfg = self.config
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1,
                            rate=cfg.mic_sample_rate, input=True,
                            frames_per_buffer=cfg.mic_block_size)
            dur = (cfg.modifier_window_seconds if self.mode == "keyword"
                   else cfg.clap_window_seconds)
            label = (f"Listening for keyword '{cfg.keyword}'..."
                     if self.mode == "keyword"
                     else f"Capture {cfg.clap_pattern} clap(s) now...")
            self.status.emit(label)

            frames: List[bytes] = []
            energies: List[float] = []
            start = time.time()
            bd = cfg.mic_block_size / cfg.mic_sample_rate
            while time.time() - start < dur:
                data = stream.read(cfg.mic_block_size)
                energies.append(block_energy(data))
                self.micLevel.emit(energies[-1])
                frames.append(data)
            stream.stop_stream(); stream.close(); p.terminate()

            if self.mode == "keyword":
                ad = sr.AudioData(b"".join(frames), cfg.mic_sample_rate, 2)
                try:
                    phrase = sr.Recognizer().recognize_google(ad).lower()
                except sr.UnknownValueError:
                    phrase = ""
                except sr.RequestError as ex:
                    self.error.emit(f"Speech recognition error (network?): {ex}")
                    return
                self.done.emit("keyword", phrase)
            else:
                count, _ = self.system.clap.analyze(energies, bd)
                self.done.emit("claps", count)
        except Exception as ex:
            self.error.emit(str(ex))


class DashboardTab(QWidget):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        self.worker = worker
        self.capture: Optional[LiveCaptureThread] = None
        lay = QVBoxLayout(self)

        self.state_lbl = QLabel("STATE: IDLE")
        self.state_lbl.setStyleSheet("font-size:22px;font-weight:bold;padding:8px;")
        lay.addWidget(self.state_lbl)

        # mic level meter (lets you SEE detection accuracy in real time)
        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 3000)
        self.mic_bar.setValue(0)
        lay.addWidget(QLabel("Mic level (live):"))
        lay.addWidget(self.mic_bar)

        self.countdown_lbl = QLabel("")
        self.countdown_lbl.setStyleSheet("font-size:40px;color:#c62828;font-weight:bold;")
        self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.countdown_lbl)

        self.cancel_btn = QPushButton("CANCEL EMERGENCY")
        self.cancel_btn.setStyleSheet("background:#c62828;color:white;font-size:18px;padding:10px;")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel)
        lay.addWidget(self.cancel_btn)

        self.last_lbl = QLabel("Last event: —")
        lay.addWidget(self.last_lbl)

        # Real capture (LIVE mode, real mic)
        live = QGroupBox("Real capture (needs mic + internet for keyword)")
        ll = QVBoxLayout(live)
        rowL = QHBoxLayout()
        self.b_listen = QPushButton("1) Hear keyword (speak it)")
        self.b_listen.clicked.connect(self._live_keyword)
        self.b_claps = QPushButton("2) Capture claps (real mic)")
        self.b_claps.clicked.connect(self._live_claps)
        rowL.addWidget(self.b_listen); rowL.addWidget(self.b_claps)
        ll.addLayout(rowL)
        self.live_status = QLabel("")
        ll.addWidget(self.live_status)
        lay.addWidget(live)

        # Simulated controls (deterministic, no mic)
        sim = QGroupBox("Simulated input (no mic needed)")
        slay = QVBoxLayout(sim)
        row1 = QHBoxLayout()
        self.kw_edit = QLineEdit(worker.config_store.current.keyword)
        row1.addWidget(QLabel("Keyword:"))
        row1.addWidget(self.kw_edit)
        b_kw = QPushButton("Hear keyword")
        b_kw.clicked.connect(lambda: self.worker.inject_keyword(self.kw_edit.text() or None))
        row1.addWidget(b_kw)
        slay.addLayout(row1)

        row2 = QHBoxLayout()
        self.clap_spin = QSpinBox(); self.clap_spin.setRange(0, 10); self.clap_spin.setValue(2)
        row2.addWidget(QLabel("Claps:"))
        row2.addWidget(self.clap_spin)
        b_clap = QPushButton("Hear claps")
        b_clap.clicked.connect(lambda: self.worker.inject_claps(self.clap_spin.value()))
        row2.addWidget(b_clap)
        slay.addLayout(row2)

        row3 = QHBoxLayout()
        self.mod_edit = QLineEdit("i need medical help")
        row3.addWidget(QLabel("Modifier:"))
        row3.addWidget(self.mod_edit)
        b_mod = QPushButton("Hear modifier")
        b_mod.clicked.connect(lambda: self.worker.inject_modifier(self.mod_edit.text() or None))
        row3.addWidget(b_mod)
        slay.addLayout(row3)

        row4 = QHBoxLayout()
        b_tick = QPushButton("Tick 1s"); b_tick.clicked.connect(self.worker.tick)
        b_auto = QPushButton("Auto-run full flow"); b_auto.clicked.connect(self._auto)
        row4.addWidget(b_tick); row4.addWidget(b_auto)
        slay.addLayout(row4)
        lay.addWidget(sim)

        # IoT-device proxy: the DISPATCH the wall device would broadcast
        disp = QGroupBox("Dispatch (IoT-device proxy)")
        dlay = QVBoxLayout(disp)
        self.dispatch_view = QTextEdit()
        self.dispatch_view.setReadOnly(True)
        self.dispatch_view.setPlainText("No dispatch yet.")
        dlay.addWidget(self.dispatch_view)
        lay.addWidget(disp)

        # timers
        self.cd_timer = QTimer(); self.cd_timer.setInterval(1000)
        self.cd_timer.timeout.connect(self.worker.tick)
        self.cd_timer.timeout.connect(self._refresh)

        worker.stateChanged.connect(self._on_state)
        worker.systemEvent.connect(self._on_event)
        worker.logEntry.connect(lambda e: None)

    # ---- live handlers (run capture in a background thread) ----
    def _start_capture(self, mode: str):
        if self.capture and self.capture.isRunning():
            return
        self.b_listen.setEnabled(False)
        self.b_claps.setEnabled(False)
        self.capture = LiveCaptureThread(
            mode, self.worker.config_store.current, self.worker.system)
        self.capture.micLevel.connect(lambda v: self.mic_bar.setValue(int(min(v, 3000))))
        self.capture.status.connect(self.live_status.setText)
        self.capture.done.connect(self._on_capture_done)
        self.capture.error.connect(lambda e: QMessageBox.warning(self, "Mic error", e))
        self.capture.finished.connect(self._capture_finished)
        self.capture.start()

    def _capture_finished(self):
        self.b_listen.setEnabled(True)
        self.b_claps.setEnabled(True)

    def _live_keyword(self):
        self._start_capture("keyword")

    def _live_claps(self):
        if self.worker.system.state not in ("KEYWORD", "CLAP_VERIFY"):
            QMessageBox.information(self, "First say keyword",
                                   "Press 'Hear keyword' (or simulate it) before capturing claps.")
            return
        self._start_capture("claps")

    def _on_capture_done(self, mode: str, value):
        if mode == "keyword":
            kw = self.worker.config_store.current.keyword
            if keyword_recognized(value, kw):
                self.live_status.setText(f"Heard: {value}")
                self.worker.inject_keyword(value)
            else:
                self.live_status.setText(f"Heard '{value}' — not the keyword, try again")
        else:  # claps
            self.live_status.setText(f"Detected {value} clap(s)")
            self.worker.inject_claps(value)

    def _on_state(self, state: str):
        self.state_lbl.setText(f"STATE: {state}")
        color = STATE_COLORS.get(state, "#333")
        self.state_lbl.setStyleSheet(
            f"font-size:22px;font-weight:bold;padding:8px;color:{color};")
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
            self.countdown_lbl.setText(f"{data.get('remaining')}s")
        elif name == "countdown_start":
            self.countdown_lbl.setText(f"{data.get('seconds')}s")
        elif name == "alert":
            self.countdown_lbl.setText("ALERT SENT")
            event = data.get("event", {})
            d = build_dispatch(event)
            self.dispatch_view.setPlainText(format_dispatch(d))
            self.last_lbl.setText(f"Last event: ALERT ({event.get('category')})")
            QMessageBox.warning(self, "Emergency Alert (SIMULATED)",
                                format_dispatch(d))
        elif name == "cancelled":
            self.countdown_lbl.setText("CANCELLED")
            self.dispatch_view.setPlainText("DISPATCH CANCELLED - no alert sent.")
            self.last_lbl.setText("Last event: CANCELLED")
        elif name == "clap_fail":
            self.last_lbl.setText("Last event: clap mismatch (reset)")
        elif name == "reset":
            self.mic_bar.setValue(0)

    def _refresh(self):
        if self.worker.is_counting_down():
            self.countdown_lbl.setText(f"{self.worker.system.alert.remaining}s")
        else:
            self.cd_timer.stop()
            self.cancel_btn.setEnabled(False)

    def _cancel(self):
        self.worker.cancel()

    def _auto(self):
        self.worker.inject_keyword(self.kw_edit.text() or None)
        self.worker.inject_claps(self.clap_spin.value())
        self.worker.inject_modifier(self.mod_edit.text() or None)


class SettingsTab(QWidget):
    def __init__(self, worker: EngineWorker):
        super().__init__()
        self.worker = worker
        lay = QVBoxLayout(self)
        cs = worker.config_store
        cfg = cs.current

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list(cs.profiles.keys()))
        self.profile_combo.setCurrentText(cs.active)
        self.profile_combo.currentTextChanged.connect(self._load_profile)
        lay.addWidget(QLabel("Active profile:")); lay.addWidget(self.profile_combo)

        self.kw = QLineEdit(cfg.keyword)
        self.thr = QSlider(Qt.Orientation.Horizontal); self.thr.setRange(100, 3000)
        self.thr.setValue(cfg.threshold)
        self.pat = QSpinBox(); self.pat.setRange(1, 10); self.pat.setValue(cfg.clap_pattern)
        self.cd = QSpinBox(); self.cd.setRange(1, 60); self.cd.setValue(cfg.countdown_seconds)

        for w, lbl in [(self.kw, "Emergency keyword:"), (self.thr, "Clap threshold:"),
                       (self.pat, "Required claps:"), (self.cd, "Countdown seconds:")]:
            lay.addWidget(QLabel(lbl)); lay.addWidget(w)

        btn = QPushButton("Save profile")
        btn.clicked.connect(self._save)
        lay.addWidget(btn)
        self.status = QLabel(""); lay.addWidget(self.status)

        self.cats = QTextEdit()
        self.cats.setPlainText(self._cats_text(cfg))
        self.cats.setReadOnly(True)
        lay.addWidget(QLabel("Configured categories (fire/health/danger):"))
        lay.addWidget(self.cats)

    def _cats_text(self, cfg):
        return "\n".join(f"{k}: {', '.join(v)}" for k, v in cfg.categories.items())

    def _load_profile(self, name):
        self.worker.config_store.set_active(name)
        cfg = self.worker.config_store.current
        self.kw.setText(cfg.keyword); self.thr.setValue(cfg.threshold)
        self.pat.setValue(cfg.clap_pattern); self.cd.setValue(cfg.countdown_seconds)
        self.cats.setPlainText(self._cats_text(cfg))

    def _save(self):
        cfg = self.worker.config_store.current
        cfg.keyword = self.kw.text().strip() or cfg.keyword
        cfg.threshold = self.thr.value()
        cfg.clap_pattern = self.pat.value()
        cfg.countdown_seconds = self.cd.value()
        store = self.worker.config_store
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "mteas_config.json")
        store.save(path)
        self.status.setText(f"Saved profile '{store.active}' to {path}")


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
        self.resize(760, 640)
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
        store = ConfigStore.default()
    log_path = os.path.join(base, "emergency_events.log")
    worker = EngineWorker(store, log_path)
    win = MainWindow(worker)
    win.show()
    rc = app.exec()
    sys.exit(rc)


if __name__ == "__main__":
    main()
