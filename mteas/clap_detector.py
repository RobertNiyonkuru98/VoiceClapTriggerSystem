"""Clap detection (FR2.x).

The core is `detect_claps`, a PURE function over a precomputed energy series so
it can be unit-tested without a microphone. Live audio simply converts mic PCM
bytes into per-block energy (`block_energy`) and feeds this function.
"""
from __future__ import annotations

from typing import List, Tuple


def block_energy(pcm_bytes: bytes) -> float:
    """Average absolute amplitude of one PCM int16 block."""
    import array
    samples = array.array("h")
    samples.frombytes(pcm_bytes)
    if not samples:
        return 0.0
    return sum(abs(s) for s in samples) / len(samples)


def detect_claps(
    energy_per_block: List[float],
    block_duration_s: float,
    threshold: float,
    refractory_s: float = 0.25,
    release_factor: float = 0.5,
) -> Tuple[int, List[float]]:
    """Count clap onsets in an energy series.

    A clap is a rising edge above `threshold`, followed by a release below
    `threshold * release_factor` and a refractory gap of `refractory_s` before
    the next clap can register. Returns (count, list_of_clap_times_seconds).
    """
    count = 0
    times: List[float] = []
    active = False
    last_clap_t = -1e9
    for i, e in enumerate(energy_per_block):
        t = i * block_duration_s
        if e >= threshold and not active:
            if t - last_clap_t >= refractory_s:
                count += 1
                times.append(round(t, 3))
                last_clap_t = t
            active = True
        elif e < threshold * release_factor:
            active = False
    return count, times


class ClapDetector:
    def __init__(self, threshold: int = 700, refractory_s: float = 0.25):
        self.threshold = threshold
        self.refractory_s = refractory_s

    def analyze(self, energy_per_block: List[float], block_duration_s: float
                ) -> Tuple[int, List[float]]:
        return detect_claps(
            energy_per_block, block_duration_s, self.threshold, self.refractory_s
        )
