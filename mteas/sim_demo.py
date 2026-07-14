"""Headless simulated demo of the full MTEAS workflow (no mic needed).

Run:  python -m mteas.sim_demo
Drives the state machine through keyword -> claps -> modifier -> countdown,
then shows BOTH outcomes: activation and cancellation.
"""
from __future__ import annotations

import os
import tempfile

from .configuration import ConfigStore
from .emergency_system import EmergencySystem
from .event_logger import EventLogger


def _print_observer(name, data):
    print(f"  [event] {name}: {data}")


def run_full_flow(cancel: bool):
    tmp = os.path.join(tempfile.gettempdir(), f"mteas_demo_{os.getpid()}.log")
    if os.path.exists(tmp):
        os.remove(tmp)
    cfg = ConfigStore.default()
    logger = EventLogger(tmp)
    system = EmergencySystem(cfg, logger)
    system.on(_print_observer)

    print(f"\n=== Simulated flow (cancel={cancel}) ===")
    system.inject_keyword("help")                    # FR1
    system.inject_claps(2)                           # FR2 (pattern=2)
    system.inject_modifier("i need medical help")    # FR3 -> health
    while system.alert.is_active():
        rem = system.tick_countdown()
        print(f"  countdown: {rem}s remaining")
        if cancel and rem == system.config.countdown_seconds - 1:
            system.cancel()
            break
    print(f"  log entries written: {len(logger.read_all())}")
    return logger.read_all()


if __name__ == "__main__":
    run_full_flow(cancel=False)
    run_full_flow(cancel=True)
    print("\nDemo complete.")
