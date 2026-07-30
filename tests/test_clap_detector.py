import unittest

from mteas.clap_detector import (
    detect_claps, ClapDetector, block_energy,
    suggest_threshold, moving_average,
)

SR = 44100
BLOCK = 1024
DUR = BLOCK / SR  # ~0.0232 s per block


def make_series(spikes, length=40, baseline=100, peak=5000, burst=3):
    """spikes = start indices of short clap bursts (length `burst` blocks)."""
    s = [baseline] * length
    for start in spikes:
        for i in range(burst):
            if 0 <= start + i < length:
                s[start + i] = peak
    return s


class TestDetectClaps(unittest.TestCase):
    def test_two_separate_claps(self):
        # bursts at 0 and 15 -> ~0.30s apart > refractory 0.25s
        count, times = detect_claps(make_series([0, 15]), DUR, threshold=1000)
        self.assertEqual(count, 2)
        self.assertEqual(len(times), 2)

    def test_claps_within_refractory_count_once(self):
        # bursts at 0 and 5 -> ~0.12s apart < refractory -> merged
        count, _ = detect_claps(make_series([0, 5]), DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_all_below_threshold(self):
        count, _ = detect_claps(make_series([], length=20), DUR, threshold=1000)
        self.assertEqual(count, 0)

    def test_sustained_loud_counts_once(self):
        # a long plateau above threshold = one clap (one run)
        series = [100] * 10 + [9000] * 10 + [100] * 10
        count, _ = detect_claps(series, DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_clapdetector_wrapper(self):
        d = ClapDetector(threshold=1000)
        count, _ = d.analyze(make_series([0, 15]), DUR)
        self.assertEqual(count, 2)

    def test_block_energy_zero_on_empty(self):
        self.assertEqual(block_energy(b""), 0.0)

    def test_two_claps_in_noisy_room(self):
        # REAL bug: room stays loud between the two claps, so old edge+release
        # detector scored 1. New run/peak detector must score 2.
        sr = 44100; block = 1024; dur = block / sr
        series = [120] * 60
        for i in range(3):
            series[10 + i] = 9000   # clap 1 burst
        for i in range(3):
            series[40 + i] = 9000   # clap 2 burst, ~0.7s later, room still ~120
        # add sustained mid noise to mimic a reverberant room
        for i in range(20, 55):
            series[i] = max(series[i], 600)
        count, times = detect_claps(series, dur, threshold=1000)
        self.assertEqual(count, 2)

    def test_suggest_threshold_from_ambient(self):
        # quiet room -> high factor above p95
        amb = [80] * 50 + [400] * 3  # mostly quiet, a few bumps
        thr = suggest_threshold(amb)
        self.assertGreater(thr, 400)
        # dead quiet -> clamped to min
        self.assertGreaterEqual(suggest_threshold([10] * 20), 300)
        # very loud ambient -> clamped to max
        self.assertLessEqual(suggest_threshold([2900] * 20), 3000)

    def test_calibrate_sets_threshold(self):
        d = ClapDetector(threshold=700)
        thr = d.calibrate([90] * 40 + [500] * 2)
        self.assertEqual(d.threshold, thr)
        self.assertNotEqual(thr, 700)

    def test_moving_average_preserves_peaks(self):
        sm = moving_average([100, 100, 9000, 100, 100])
        self.assertGreater(sm[2], 1000)


if __name__ == "__main__":
    unittest.main()
