# Design Decisions Log : MTEAS (Multi-Trigger Emergency Assistance System)

This doc records architectural decisions so the team / course facilitator can
trace WHY a choice was made. Requirement COVERAGE is tracked separately in
`docs/SRS_TRACEABILITY.md`.

---

## D1 : Keyword detection: Google SR + SIMULATED inject mode (2026-07-14)
- **Decision**: Keep `SpeechRecognition` (Google Web Speech) for LIVE keyword
  detection : it matches the existing repo and is the lowest-effort path. Add a
  **simulated inject mode** to `EmergencySystem` so the FULL SRS workflow
  (keyword -> clap -> modifier -> countdown -> alert/cancel -> log) is drivable
  deterministically WITHOUT a microphone or network.
- **Rationale**: The priority is a reliable, demoable, testable system by
  Tue 2026-07-21 (target ~70%). Google SR is also explicitly in the SRS
  library list (§3.3). A simulated mode makes unit tests real and the demo
  independent of flaky mic/network conditions.
- **Consequence**: Live demo still needs internet + mic; simulated demo needs
  neither. Offline keyword detection (Vosk) is a documented future upgrade
  that improves NFR1 (realtime/low-latency) and removes the network dependency.

## D2 : Cancellation countdown is TICK-DRIVEN and pure (2026-07-14)
- **Decision**: `AlertManager` exposes `begin()`, `tick()` (advances 1s),
  `cancel()`, `is_active()`. The orchestrator calls `tick()` once per second.
  In the GUI this is driven by a `QTimer`; in tests it is driven by a loop.
- **Rationale**: Keeps `AlertManager` free of `time.sleep`/threading so it is
  fully unit-testable and the same code runs in the GUI. Directly serves
  FR4.1–FR4.4 and NFR2.1 (cancellation window) and NFR5.2 (cancel only in window).

## D3 : Clap detection is a PURE function over an energy series (2026-07-14)
- **Decision**: `detect_claps(energy_per_block, block_duration_s, threshold,
  refractory_s)` is a pure function returning `(count, times)`. Live audio
  converts mic PCM -> per-block energy (`block_energy`) and feeds this function.
- **Rationale**: The crude `peak > 700` check in the old repo double-counts and
  misses fast claps. A refractory + release-hysteresis onset detector is robust
  and, crucially, TESTABLE with synthetic energy (no mic). Satisfies FR2.1/2.2
  and improves NFR1.2.

## D4 : Alert is SIMULATED, never a real action (2026-07-14)
- **Decision**: `_trigger_alert()` only logs + emits an event + (later) shows a
  GUI banner/sound. It NEVER launches apps or kills processes (unlike the old
  3-clap->Steam behaviour, which violated NFR2/NFR5).
- **Rationale**: SRS FR4.5 says "trigger a SIMULATED emergency alert". The
  prototype must not perform irreversible actions without confirmation, and
  every activation is gated behind full layered verification + countdown.

## D5 : Event logging is append-only JSONL (2026-07-14)
- **Decision**: `EventLogger` appends one JSON object per line to a `.log` file
  (never overwrites), with a thread-safe lock and an observer callback for live
  GUI updates.
- **Rationale**: Satisfies FR5.1–FR5.5 and NFR3.2 (secure/append-only logs) and
  NFR5.3 (mandatory logging of all outcomes). The observer lets the PyQt6 log
  viewer update live.

## D9 : Spoken feedback restores the original "yes" voice (2026-07-20)
- The original `main.py` (archived to `legacy_voice_assistant/`) used `pyttsx3`
  to speak "Yes Boss!" on keyword capture, then ran claps/modifier/app-launch.
  The MTEAS GUI dropped that, leaving the hands-free flow silent/confusing.
- Fix: re-added a `Voice` helper (gui/app.py) that speaks step prompts on the
  real listener path: keyword heard -> "Begin the N clap sequence"; clap count;
  "Clap sequence over, speak the modifier"; dispatch -> "Emergency triggered".
  pyttsx3 is imported lazily and `speak()` is a no-op if unavailable, so the GUI
  never crashes without audio/pyttsx3.
- Config seeded from the original `config.py` on first run: keyword="jesus"
  (WAKE_WORD), threshold=500, persisted to `mteas_config.json`. The user's
  trained keyword now matches (the GUI previously defaulted to "help").
- Clap capture feeds the mic meter live; 0 claps re-prompts instead of advancing
  (was a bug: state jumped to CLAP_VERIFY/COUNTDOWN with no claps).

## D8 : Always-on listener + real email dispatch (2026-07-20)
- **Product mental model (user)**: the device is ALWAYS LISTENING. One "Start
  Listening" click powers the session; the trigger then runs HANDS-FREE from real
  sound (keyword -> claps -> optional modifier -> countdown -> dispatch). The GUI
  is the RESPONDER CONSOLE, not a click-to-trigger harness.
- **Impl**: `ListenerThread` (gui/app.py) keeps the mic open in a loop, calibrates
  to room noise, detects keyword (Google now / Vosk selectable), captures claps,
  optional modifier, and lets the engine run the countdown. `KeywordDetector`
  gained a `keyword_engine` ("google"|"vosk") : Vosk is offline (no network),
  lazy-imported so the dep is optional.
- **Email dispatch (FR6.2/FR6.3)**: `mteas/dispatcher.py` sends the dispatch
  record via SMTP when `Configuration.dispatch_channel == "email"` and a
  responder + creds are set. Default channel is "simulated" (D4) : NO real email
  leaves the machine unless explicitly configured via env vars
  (MTEAS_SMTP_USER/PASS/HOST/PORT) or a .env. Tests use a fake SMTP server.
- **Safety**: the old click-to-trigger buttons ("Hear keyword", "Hear claps")
  were removed from the main UI; they survive only in a collapsed
  "Developer / Test" panel for deterministic no-mic demos (decision D1).
- **DB**: deliberately NOT used. FR5 (mandatory logging) satisfied by the
  append-only JSONL log. A relational DB is deferred to the production IoT
  rollout (FR6) where responder/user tables + audit querying are required.

## D7 : IoT device is a LOCATION shift, not a behaviour change (2026-07-14)
- **Model**: 3 layers : SENSOR (mic) → ENGINE (detect/verify) → DISPATCH (alert).
  Only the SENSOR host + DISPATCH channel change over time:
    NOW   : laptop inbuilt mic + `mteas/` app + PyQt6 GUI as dispatch proxy
    FUTURE: wall/IoT device (mic + speaker + GSM + backup battery + optional
            physical button) on the same engine, real SMS/GSM/center channels (FR6)
- **Key point (student-confirmed)**: the wall device does NOT change the INPUT
  method : it captures the same keyword+clap+modifier+countdown sound. The
  laptop-mic prototype IS the future behaviour, just hosted on a laptop.
- **Parallel trigger**: SRS 3.2 lists a physical emergency BUTTON as separate
  future hardware : a PARALLEL trigger (when a button IS reachable), not a
  replacement for the hands-free sound path (when it is NOT).
- **Dispatch proxy**: until real hardware exists, the GUI's DISPATCH SENT panel
  is the IoT-device proxy (see docs/IOT_ARCHITECTURE.md).

## D6 : "Simulated" = OUTPUT/dispatch layer; GUI is the IoT-device proxy (2026-07-14)
- **Clarification (student)**: The proposal's "simulation" is NOT about faking the
  audio INPUT. It refers to the **IoT device + emergency-responder backend** that
  physically do not exist yet (FR6.3/FR6.4 are FUTURE). The INPUT layer
  (keyword + clap + modifier + countdown) is REAL and works now, replacing
  slow/impossible button-dialing during distress.
- **Decision**: The PyQt6 GUI stands IN for the absent IoT device / responder
  console. A confirmed alert (after full layered verification + countdown) is
  "simulated" = recorded + shown as the dispatch the IoT device *would* have
  broadcast (category, timestamp, event id). No irreversible real action is taken
  (consistent with D4 / NFR2 / NFR5).
- **Two distinct "simulation" meanings (avoid confusing the facilitator)**:
  - (a) Simulated INPUT = `inject_*` dev/demo aid to drive the engine without a
    mic/internet. NOT a system feature.
  - (b) Simulated OUTPUT = the alert. SRS scope; GUI-as-IoT-proxy because the
    real device is unavailable.
- **Future**: a local/offline ASR server (replacing Google SR) + real IoT
  dispatch when hardware/connectivity exist (improves NFR1 realtime/low-latency
  and removes the network dependency).
