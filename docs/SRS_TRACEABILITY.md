# SRS Traceability Matrix — Multi-Trigger Emergency Assistance System (MTEAS)

Source: `Robert Tony Mitali Niyonkuru_[Proposal and SRS Document]_[W4]_[05-27-2026].pdf`
Repo (current): `/c/Users/Richter Richard NAHO/TonyRobert98/VoiceClapTriggerSystem`

Status legend: DONE = implemented & SRS-aligned · PARTIAL = structurally present but off-spec · MISSING = not implemented · CONFLICT = implemented but violates SRS

---

## 1. Functional Requirements (FR)

| ID | Requirement | SRS summary | Current repo state | Target module |
|----|-------------|-------------|--------------------|---------------|
| FR1 | Emergency keyword detection | Continuous listen for configurable keyword | PARTIAL — continuous listen exists, but wake word hardcoded "jesus", not emergency-themed | `AudioEngine` / `ConfigManager` |
| FR1.1 | Listen for emergency keywords | Continuous listening state | DONE (loop in main.py) | `AudioEngine` |
| FR1.2 | Configurable keyword | Customize via settings | MISSING — hardcoded in config.py | `ConfigManager` + Settings GUI |
| FR1.3 | Keyword detection notification | Notify on valid detection | PARTIAL — says "Yes Boss!" (off-spec phrasing) | `AudioEngine` + GUI/voice feedback |
| FR1.4 | Initiate clap verification | Trigger clap check after keyword | DONE (count_claps after wake) | `AudioEngine` |
| FR1.5 | Reset listening mode | Revert after fail/timeout | PARTIAL — `except: continue` loops back, but no clean state reset | `StateMachine` |
| FR2 | Clap pattern verification | Verify intent via clap pattern | PARTIAL — counts claps, but "pattern" = raw count, no predefined patterns/retry | `ClapDetector` |
| FR2.1 | Detect clap sequence | Detect claps via mic | PARTIAL — crude peak>THRESHOLD, not robust onset | `ClapDetector` |
| FR2.2 (dup id) | Time-limited verification | Verify within time window | PARTIAL — 4s window exists | `ClapDetector` |
| FR2.3 | Predefined clap patterns | Support predefined patterns | MISSING — uses count only, no pattern semantics | `ClapPattern` config |
| FR2.4 | Failed verification notification | Notify on failure | MISSING | `AudioEngine`/GUI |
| FR2.5 | Retry clap confirmation | Retry after failure | MISSING | `StateMachine` |
| FR2.6 | Verification timeout reset | Reset after repeated fail | MISSING | `StateMachine` |
| FR3 | Emergency modifier processing | Modifier words for category | PARTIAL — modifier word captured, but maps to launch actions, not emergency categories | `ModifierProcessor` |
| FR3.1 | Detect modifier words | Optional modifier detection | DONE (recognize_google) | `ModifierProcessor` |
| FR3.2 | Emergency category identification | fire/health/danger | MISSING — no category mapping | `ModifierProcessor` |
| FR3.3 | Modifier input window | Process within time | PARTIAL — 2s window exists | `ModifierProcessor` |
| FR4 | Emergency alert workflow | Simulate alert activation | CONFLICT — current 3-clap opens Steam (irreversible, no confirmation) | `AlertManager` |
| FR4.1 | Countdown initialization | Cancellation countdown before finalize | MISSING — biggest gap | `AlertManager` |
| FR4.2 | Configurable countdown duration | Duration modifiable | MISSING | `ConfigManager` |
| FR4.3 | Countdown display | Show countdown status | MISSING | GUI + voice |
| FR4.4 | Emergency cancellation | Cancel during countdown | MISSING — critical safety feature | `AlertManager` + GUI |
| FR4.5 | Trigger simulated alert | Fire alert if not cancelled | MISSING — must be SIMULATED, not real launch | `AlertManager` |
| FR4.6 | Alert confirmation message | Show confirmation | MISSING | GUI + voice |
| FR5 | Event logging | Record emergency activities | MISSING — no logging at all | `EventLogger` |
| FR5.1 | Log event timestamps | Timestamp events | MISSING | `EventLogger` |
| FR5.2 | Log detected keywords | Record keyword/modifier | MISSING | `EventLogger` |
| FR5.3 | Log successful activations | Record activations | MISSING | `EventLogger` |
| FR5.4 | Log cancelled alerts | Record cancellations | MISSING | `EventLogger` |
| FR5.5 | Log detection errors | Record failures/errors | MISSING | `EventLogger` |
| FR6 | Future comms integration | SMS/Email/IoT/center | FUTURE — not in prototype scope | (stub/interface only) |

---

## 2. Non-Functional Requirements (NFR)

| ID | Type | SRS summary | Current repo | Gap |
|----|------|-------------|--------------|-----|
| NFR1 | Performance | Realtime detection, low latency, immediate feedback | PARTIAL — works but Google SR adds latency + needs network | Local/offline keyword detection option |
| NFR1.1 | Realtime keyword | Low delay | PARTIAL | — |
| NFR1.2 | Clap processing speed | Short window | PARTIAL | — |
| NFR1.3 | Immediate feedback | Alerts/countdowns right after event | MISSING (no countdown) | GUI feedback |
| NFR2 | Safety | Minimize accidental activation | CONFLICT — 3-clap→Steam is irreversible & unconfirmed | Cancellation window (FR4.4) |
| NFR2.1 | Cancellation window | Cancel period before finalize | MISSING | FR4.4 |
| NFR2.2 | Layered verification | keyword + clap | DONE structurally | — |
| NFR2.3 | Safe reset | Return to listen on fail | PARTIAL | `StateMachine` |
| NFR2.4 | Controlled alert activation | No irreversible action w/o confirmation | CONFLICT — Steam launch | FR4 workflow |
| NFR3 | Security | Protect config & logs | MISSING — config world-readable, no log integrity | Config access + append-only log |
| NFR3.1 | Protected config | Restrict unauthorized changes | MISSING | Settings auth/lock |
| NFR3.2 | Secure event logs | Prevent accidental log change | MISSING | Append-only logger |
| NFR4 | Quality | Usability/Reliability/Maintainability/Scalability | PARTIAL — not modular, no tests, no GUI | Modular + PyQt6 GUI + tests |
| NFR4.1 | Usability | Clear feedback | PARTIAL (print only) | PyQt6 GUI |
| NFR4.2 | Reliability | Stable repeated operation | UNKNOWN — no tests | Tests |
| NFR4.3 | Maintainability | Modular components | PARTIAL — tangled main/actions | Modular refactor |
| NFR4.4 | Scalability | Future IoT/mobile/cloud | MISSING | Interface seams |
| NFR5 | Business rules | Trigger only after full verification; cancel only in window; mandatory logging; comms only after verification | CONFLICT/Missing | Enforce in `StateMachine` |

---

## 3. Key finding
The current repo implements a **personal productivity launcher** (study/coding/gaming/social, wake word "jesus", 3-clap opens Steam). The SRS specifies an **emergency assistance system** with layered verification AND a **cancellation countdown** before any alert, plus **mandatory event logging**. The audio/keyword/clap/modifier *skeleton* is reusable, but the actions, safety model, and logging must be rebuilt to match the SRS. The 3-clap→Steam behavior directly violates NFR2/NFR5.
