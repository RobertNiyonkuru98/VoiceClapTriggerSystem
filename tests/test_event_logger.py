import os
import tempfile
import unittest

from mteas.emergency_event import EmergencyEvent
from mteas.event_logger import EventLogger


class TestEventLogger(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.gettempdir(), "mteas_log_test.log")
        if os.path.exists(self.path):
            os.remove(self.path)
        self.log = EventLogger(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_log_and_read(self):
        self.log.log_keyword("help")
        self.log.log_clap(2)
        self.log.log_modifier("medical help", "health")
        self.log.log_activation(EmergencyEvent(outcome="activated", category="health"))
        self.log.log_cancellation(EmergencyEvent(outcome="cancelled"))
        self.log.log_error("boom")
        entries = self.log.read_all()
        self.assertEqual(len(entries), 6)
        self.assertEqual(entries[0]["type"], "keyword")
        self.assertEqual(entries[2]["category"], "health")

    def test_append_only_accumulates(self):
        self.log.log_keyword("a")
        self.log.log_keyword("b")
        self.assertEqual(len(self.log.read_all()), 2)

    def test_observer_called(self):
        seen = []
        self.log.on_log(lambda e: seen.append(e))
        self.log.log_keyword("help")
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["type"], "keyword")


if __name__ == "__main__":
    unittest.main()
