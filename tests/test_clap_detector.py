import unittest

from mteas.clap_detector import detect_claps, ClapDetector, block_energy

SR = 44100
BLOCK = 1024
DUR = BLOCK / SR  # ~0.0232 s per block


def make_series(spikes, length=40, baseline=100, peak=5000):
    s = [baseline] * length
    for i in spikes:
        s[i] = peak
    return s


class TestDetectClaps(unittest.TestCase):
    def test_two_separate_claps(self):
        # spikes at 0 and 11 -> gap ~0.255s > refractory 0.25s
        count, times = detect_claps(make_series([0, 11]), DUR, threshold=1000)
        self.assertEqual(count, 2)
        self.assertEqual(len(times), 2)

    def test_claps_within_refractory_count_once(self):
        # spikes at 0 and 5 -> gap ~0.116s < refractory
        count, _ = detect_claps(make_series([0, 5]), DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_all_below_threshold(self):
        count, _ = detect_claps(make_series([], length=20), DUR, threshold=1000)
        self.assertEqual(count, 0)

    def test_sustained_loud_counts_once(self):
        # a long plateau above threshold = one clap (rising edge only)
        series = [100] * 10 + [9000] * 10 + [100] * 10
        count, _ = detect_claps(series, DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_clapdetector_wrapper(self):
        d = ClapDetector(threshold=1000)
        count, _ = d.analyze(make_series([0, 11]), DUR)
        self.assertEqual(count, 2)

    def test_block_energy_zero_on_empty(self):
        self.assertEqual(block_energy(b""), 0.0)


if __name__ == "__main__":
    unittest.main()
