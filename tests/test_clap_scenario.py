"""Deterministic proof that clap detection is accurate (no mic needed).

These tests simulate the LISTENING state with a known energy signal and assert the
exact clap count. This is the "simulate the app's listening state to prove
accuracy" scenario: we feed a synthetic mic energy stream that mimics real claps
and confirm detection.
"""
import unittest

from mteas.clap_detector import detect_claps, block_energy, ClapDetector

SR = 44100
BLOCK = 1024
DUR = BLOCK / SR  # ~0.0232s per block


def build_signal(events, blocks_per_clap=4, gap_blocks=15, baseline=80, peak=6000):
    """Build an energy series from a list of clap onsets (block index, is_clap).

    `events` is a list of (start_block, is_clap). For claps we emit a short
    loud burst; for silence we keep baseline. Between claps there is `gap_blocks`
    of quiet so successive claps are separated in time.
    """
    length = sum(
        (blocks_per_clap + gap_blocks) if is_c else 0 for _, is_c in events
    ) + 20
    sig = [baseline] * length
    pos = 0
    for start, is_c in events:
        if is_c:
            for i in range(blocks_per_clap):
                sig[pos + i] = peak
            pos += blocks_per_clap + gap_blocks
    return sig


class TestClapScenario(unittest.TestCase):
    def test_three_realistic_claps(self):
        # 3 claps, each a short burst separated by silence > refractory
        sig = build_signal([(0, True), (0, True), (0, True)])
        count, times = detect_claps(sig, DUR, threshold=1000)
        self.assertEqual(count, 3)
        self.assertEqual(len(times), 3)

    def test_single_clap(self):
        sig = build_signal([(0, True)])
        count, _ = detect_claps(sig, DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_no_clap_in_silence(self):
        sig = [80] * 100  # pure silence below threshold
        count, _ = detect_claps(sig, DUR, threshold=1000)
        self.assertEqual(count, 0)

    def test_background_noise_not_counted(self):
        # low-level noise (below threshold) must not register
        import random
        sig = [random.randint(100, 500) for _ in range(200)]
        count, _ = detect_claps(sig, DUR, threshold=1000)
        self.assertEqual(count, 0)

    def test_rapid_double_clap_counts_once(self):
        # two bursts within refractory window -> 1 clap
        sig = [80] * 60
        for i in range(4):
            sig[i] = 6000
        for i in range(4):
            sig[i + 6] = 6000  # ~0.14s later < 0.25s refractory
        count, _ = detect_claps(sig, DUR, threshold=1000)
        self.assertEqual(count, 1)

    def test_threshold_sensitivity(self):
        sig = build_signal([(0, True)])
        # too-high threshold -> missed
        self.assertEqual(detect_claps(sig, DUR, threshold=9000)[0], 0)
        # appropriate threshold -> detected
        self.assertEqual(detect_claps(sig, DUR, threshold=1000)[0], 1)

    def test_block_energy_realistic_pcm(self):
        import array
        # a loud int16 block
        samples = array.array("h", [30000] * 100)
        raw = samples.tobytes()
        self.assertGreater(block_energy(raw), 10000)
        # a quiet block
        quiet = array.array("h", [10] * 100).tobytes()
        self.assertLess(block_energy(quiet), 100)


if __name__ == "__main__":
    unittest.main()
