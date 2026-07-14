# Multi-Trigger Emergency Assistance System (MTEAS)

A layered-verification emergency assistance **prototype** (Python / Windows).
Say a configurable emergency **keyword**, confirm with a **clap pattern**, optionally
say a **modifier** (fire / health / danger), then a **cancellation countdown**
gives a final chance to abort before a **simulated** alert is logged.

This matches the SRS (`Robert Tony Mitali Niyonkuru_[Proposal and SRS
Document]_[W4]_[05-27-2026].pdf`). The older `main.py` / `actions.py` /
`config.py` were a productivity-launcher prototype and are being superseded by the
modular `mteas/` package documented below.

## Architecture (maps to SRS class diagram)
```
EmergencySystem (controller / state machine)
   ├─ KeywordDetector   FR1  continuous keyword listen (+ inject mode)
   ├─ ClapDetector      FR2  onset-based clap counting (testable)
   ├─ ModifierProcessor FR3  fire/health/danger classification
   ├─ AlertManager      FR4  tick-driven cancellation countdown
   ├─ EventLogger       FR5  append-only JSONL event log
   └─ Configuration     NFR3 configurable profiles (JSON)
gui/ (PyQt6)            NFR4.1 usability — Dashboard / Settings / Event Log
```

State machine: `IDLE -> KEYWORD -> CLAP_VERIFY -> MODIFIER -> COUNTDOWN -> (ALERT | CANCEL) -> IDLE`

## Run the engine (headless, no mic)
```bash
.venv/Scripts/activate
python -m mteas.sim_demo        # shows activation + cancellation flows
python -m unittest discover -s tests -p "test_*.py"   # 25 tests
```

## Run the GUI (PyQt6)
```bash
.venv/Scripts/activate
python -m gui.app
```
Use the **Dashboard > Simulated input** panel to drive the whole workflow without
a microphone. The **Settings** tab configures keyword / threshold / clap pattern /
countdown and manages profiles (saved to `mteas_config.json`). The **Event Log**
tab shows the append-only log (`emergency_events.log`).

## Why a "simulated" alert?
The SRS (FR4.5) requires a *simulated* alert — the prototype must not perform
irreversible real actions. Every activation is gated behind full layered
verification + a cancellation window (NFR2, NFR5).

## Docs
- `docs/SRS_TRACEABILITY.md` — every FR/NFR mapped to module + status
- `docs/DESIGN_DECISIONS.md` — logged design choices
