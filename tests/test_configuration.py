import json
import os
import tempfile
import unittest

from mteas.configuration import Configuration, ConfigStore, DEFAULT_CATEGORIES


class TestConfiguration(unittest.TestCase):
    def test_defaults(self):
        c = Configuration()
        self.assertEqual(c.keyword, "help")
        self.assertEqual(c.clap_pattern, 2)
        self.assertEqual(c.categories, DEFAULT_CATEGORIES)

    def test_roundtrip_dict(self):
        c = Configuration(keyword="emergency", countdown_seconds=15)
        c2 = Configuration.from_dict(c.to_dict())
        self.assertEqual(c2.keyword, "emergency")
        self.assertEqual(c2.countdown_seconds, 15)

    def test_configstore_save_load(self):
        tmp = os.path.join(tempfile.gettempdir(), "mteas_cfg_test.json")
        if os.path.exists(tmp):
            os.remove(tmp)
        store = ConfigStore.default()
        store.current.keyword = "sos"
        store.add_profile("night", Configuration(keyword="help", countdown_seconds=5))
        store.set_active("night")
        store.save(tmp)
        loaded = ConfigStore.load(tmp)
        self.assertEqual(loaded.active, "night")
        self.assertEqual(loaded.current.keyword, "help")
        self.assertEqual(loaded.profiles["default"].keyword, "sos")
        os.remove(tmp)

    def test_set_active_unknown_raises(self):
        store = ConfigStore.default()
        with self.assertRaises(KeyError):
            store.set_active("nope")


if __name__ == "__main__":
    unittest.main()
