import unittest

from mteas.dispatch import build_dispatch, format_dispatch
from mteas.emergency_event import EmergencyEvent


class TestDispatch(unittest.TestCase):
    def test_build_from_event(self):
        ev = EmergencyEvent(event_id="abc", category="health", outcome="activated")
        d = build_dispatch(ev)
        self.assertEqual(d["event_id"], "abc")
        self.assertEqual(d["category"], "health")
        self.assertEqual(d["recipient"], "Emergency Responder")
        self.assertEqual(d["channel"], "SIMULATED")
        self.assertEqual(d["status"], "SIMULATED")

    def test_build_from_dict_payload(self):
        payload = {"event_id": "xyz", "category": "fire", "timestamp": 123.0}
        d = build_dispatch(payload, recipient="Caregiver", channel="SMS")
        self.assertEqual(d["event_id"], "xyz")
        self.assertEqual(d["recipient"], "Caregiver")
        self.assertEqual(d["channel"], "SMS")
        self.assertEqual(d["status"], "SENT")

    def test_unspecified_category(self):
        d = build_dispatch(EmergencyEvent())
        self.assertEqual(d["category"], "unspecified")

    def test_format_contains_markers(self):
        d = build_dispatch(EmergencyEvent(event_id="e1", category="danger"))
        txt = format_dispatch(d)
        self.assertIn("DISPATCH SENT", txt)
        self.assertIn("danger", txt)
        self.assertIn("SIMULATED", txt)


if __name__ == "__main__":
    unittest.main()
