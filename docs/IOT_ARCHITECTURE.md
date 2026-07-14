# IoT Architecture (Future) — MTEAS

This documents the proposed IoT device and how it relates to the current
prototype. Decided 2026-07-14 (see `docs/DESIGN_DECISIONS.md` D6, D7).

## Three layers
```
   SENSOR  (mic)      -> captures keyword + clap + modifier + countdown
        |
   ENGINE  (verify)   -> mteas/ state machine (FR1-FR5)
        |
   DISPATCH(alert)     -> send to responder / caregiver / center
```

The IoT device changes only the SENSOR *host* and the DISPATCH *channel*.
The ENGINE and the INPUT METHOD are unchanged.

## NOW vs FUTURE
| Layer   | NOW (prototype)                       | FUTURE (IoT)                                             |
|---------|---------------------------------------|----------------------------------------------------------|
| SENSOR  | laptop inbuilt mic                    | wall/IoT device mic (+ optional physical emergency button)|
| ENGINE  | `mteas/` desktop app                 | embedded on the device                                   |
| DISPATCH| PyQt6 GUI panel (SIMULATED)         | real SMS / GSM / Email / responder-center channels (FR6) |
| Power   | laptop battery/mains                  | device backup battery (SRS 2.5: outages)                |
| Output  | GUI speaker/announce                  | device speaker (countdown + cancel prompt)               |

## Key points
- The wall device does NOT change the INPUT method — it captures the same
  sound (keyword+clap+modifier+countdown). The laptop-mic prototype IS the
  future behaviour, just hosted on a laptop (student-confirmed).
- The physical emergency BUTTON (SRS 3.2) is a PARALLEL trigger for when a
  button IS reachable; the hands-free sound path is for when it is NOT.
  Both feed the same engine.
- Until real hardware exists, the GUI's DISPATCH SENT panel is the IoT-device
  proxy (D6): it shows the record the device WOULD broadcast.
- A future offline/local ASR server (replacing Google SR) lets the device work
  without internet and improves NFR1 (realtime / low latency), connecting
  "when in range" (SRS 3.4).
