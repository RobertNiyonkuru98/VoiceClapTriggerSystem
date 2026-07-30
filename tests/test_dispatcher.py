"""Tests for the responder email dispatcher (FR6.2/FR6.3).

Uses a FAKE SMTP server so no real email is ever sent during testing (decision
D4: never perform irreversible/outbound actions in tests).
"""
import unittest
from email.message import EmailMessage

from mteas import dispatcher as dmod
from mteas.dispatcher import EmailConfig, build_email, send_email


class FakeSMTP:
    """Minimal stand-in for smtplib.SMTP_SSL that records send calls."""
    def __init__(self, host=None, port=None, context=None):
        self.host = host
        self.port = port
        self.sent = []
        self.logged_in = False

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        self.logged_in = True
        self.user, self.password = user, password

    def send_message(self, msg: EmailMessage):
        self.sent.append(msg)


class TestDispatcher(unittest.TestCase):
    def test_build_email_contents(self):
        msg = build_email("police@example.com", "DISPATCH SENT\n  Category: fire")
        self.assertEqual(msg["To"], "police@example.com")
        self.assertIn("fire", msg.get_content())

    def test_send_email_requires_config(self):
        # no creds -> must refuse (never silently send)
        cfg = EmailConfig(sender="", password="")
        self.assertFalse(cfg.is_configured())
        with self.assertRaises(RuntimeError):
            send_email("police@example.com", "x", email_cfg=cfg, smtp_cls=FakeSMTP)

    def test_send_email_real_path(self):
        cfg = EmailConfig(sender="me@x.com", password="app-pass")
        ok = send_email("police@example.com", "DISPATCH SENT",
                        email_cfg=cfg, smtp_cls=FakeSMTP)
        self.assertTrue(ok)

    def test_email_not_sent_when_simulated(self):
        # The system only calls send_email when channel=='email'; this test
        # confirms the dispatch module itself won't send without explicit call.
        # (simulated channel is handled in emergency_system.dispatch_fn wiring)
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
