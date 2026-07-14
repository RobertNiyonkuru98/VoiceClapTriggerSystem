import os
import tempfile
import unittest

from mteas.configuration import ConfigStore
from mteas.emergency_system import (
    EmergencySystem,
    STATE_CLAP, STATE_COUNTDOWN, STATE_IDLE, STATE_MODIFIER,
)
from mteas.event_logger import EventLogger


class TestEmergencySystem(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "mteas_sys_test.log")
        if os.path.exists(self.path):
            os.remove(self.path)
        self.cfg = ConfigStore.default()  # keyword=help, pattern=2, countdown=10
        self.logger = EventLogger(self.path)
        self.system = EmergencySystem(self.cfg, self.logger)
        self.events = []  # (name, data)
        self.system.on(lambda n, d: self.events.append((n, d)))

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _states(self):
        return [d["state"] for n, d in self.events if n == "state"]

    def _full_flow(self, cancel=False):
        self.system.inject_keyword("help")
        self.system.inject_claps(2)
        self.system.inject_modifier("medical help")
        while self.system.alert.is_active():
            rem = self.system.tick_countdown()
            if cancel and rem == self.cfg.current.countdown_seconds - 1:
                self.system.cancel()
                break

    def test_activation_flow(self):
        self._full_flow(cancel=False)
        names = [n for n, _ in self.events]
        self.assertIn("alert", names)
        self.assertNotIn("cancelled", names)
        self.assertEqual(self.system.state, STATE_IDLE)
        types = [e["type"] for e in self.logger.read_all()]
        self.assertIn("activation", types)
        self.assertNotIn("cancellation", types)

    def test_cancellation_flow(self):
        self._full_flow(cancel=True)
        names = [n for n, _ in self.events]
        self.assertIn("cancelled", names)
        self.assertNotIn("alert", names)
        types = [e["type"] for e in self.logger.read_all()]
        self.assertIn("cancellation", types)

    def test_clap_mismatch_resets(self):
        self.system.inject_keyword("help")
        self.system.inject_claps(1)  # needs >=2
        self.assertEqual(self.system.state, STATE_IDLE)
        names = [n for n, _ in self.events]
        self.assertIn("clap_fail", names)

    def test_state_transitions_emitted(self):
        self.system.inject_keyword()
        self.system.inject_claps(2)
        self.system.inject_modifier("fire")
        states = self._states()
        self.assertIn(STATE_CLAP, states)
        self.assertIn(STATE_MODIFIER, states)
        self.assertIn(STATE_COUNTDOWN, states)


if __name__ == "__main__":
    unittest.main()
