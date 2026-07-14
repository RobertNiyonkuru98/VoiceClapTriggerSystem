import unittest

from mteas.configuration import DEFAULT_CATEGORIES
from mteas.modifier_processor import ModifierProcessor


class TestModifierProcessor(unittest.TestCase):
    def setUp(self):
        self.mp = ModifierProcessor(DEFAULT_CATEGORIES)

    def test_fire(self):
        self.assertEqual(self.mp.classify("there is a fire"), "fire")

    def test_health(self):
        self.assertEqual(self.mp.classify("i need medical help"), "health")

    def test_danger(self):
        self.assertEqual(self.mp.classify("someone is attacking me"), "danger")

    def test_none(self):
        self.assertIsNone(self.mp.classify("hello world"))
        self.assertIsNone(self.mp.classify(None))
        self.assertIsNone(self.mp.classify(""))


if __name__ == "__main__":
    unittest.main()
