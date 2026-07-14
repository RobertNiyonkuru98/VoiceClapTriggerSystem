import unittest

from mteas.alert_manager import AlertManager


class TestAlertManager(unittest.TestCase):
    def test_countdown_to_confirm(self):
        a = AlertManager(3)
        a.begin()
        self.assertTrue(a.is_active())
        self.assertEqual(a.tick(), 2)
        self.assertEqual(a.tick(), 1)
        self.assertEqual(a.tick(), 0)
        self.assertFalse(a.is_active())
        self.assertTrue(a.confirmed)

    def test_cancel_mid(self):
        a = AlertManager(5)
        a.begin()
        a.tick()
        self.assertTrue(a.cancel())
        self.assertFalse(a.is_active())
        self.assertTrue(a.cancelled)
        self.assertFalse(a.confirmed)

    def test_cancel_when_inactive(self):
        a = AlertManager(5)
        self.assertFalse(a.cancel())

    def test_tick_when_inactive(self):
        a = AlertManager(5)
        self.assertEqual(a.tick(), 0)


if __name__ == "__main__":
    unittest.main()
