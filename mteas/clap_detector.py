"""Clap detection (FR2.x).

Design goals:
  * `detect_claps` is a PURE function over a precomputed energy series so it can
    be unit-tested without a microphone (decision D1).
  * Counting is RUN/PEAK based, not rising-edge + release. A clap = one maximal
    run of blocks above threshold, separated from the next by at least a
    refractory gap. This is immune to a room where energy stays loud between
    two claps (the old bug that scored 1 for 2 claps).
  * `suggest_threshold` derives a threshold from the AMBIENT noise floor, so the
    detector auto-calibrates to the environment instead of hardcoding 700.
"""
from __future__ import annotations

import statistics
from typing import List, Tuple


def block_energy(pcm_bytes: bytes) -> float:
    """Average absolute amplitude of one PCM int16 block."""
    import array
    samples = array.array("h")
    samples.frombytes(pcm_bytes)
    if not samples:
        return 0.0
    return sum(abs(s) for s in samples) / len(samples)


def moving_average(series: List[float], window: int = 3) -> List[float]:
    half = max(1, window // 2)
    out = []
    n = len(series)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        out.append(sum(series[lo:hi]) / (hi - lo))
    return out


def suggest_threshold(ambient: List[float],
                      factor: float = 3.5,
                      min_t: float = 300.0,
                      max_t: float = 3000.0) -> int:
    """Derive a clap threshold from the ambient noise floor.

    Uses the 95th percentile of ambient energy (robust to occasional bumps)
    times `factor`. A real clap is orders of magnitude louder than ambient, so
    this separates speech/clatter from claps in *any* room. Clamped to
    [min_t, max_t] so a dead-quiet room still demands a real spike.
    """
    if not ambient:
        return int(min_t)
    ordered = sorted(ambient)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
    return int(min(max(p95 * factor, min_t), max_t))


def detect_claps(
    energy_per_block: List[float],
    block_duration_s: float,
    threshold: float,
    refractory_s: float = 0.25,
) -> Tuple[int, List[float]]:
    """Count clap onsets in an energy series (RUN/PEAK based).

    Each clap is one maximal run of blocks at/above `threshold`. Runs whose gap
    is shorter than `refractory_s` are merged into one clap (handles a double
    transient). Returns (count, list_of_clap_times_seconds).
    """
    sm = moving_average(energy_per_block, 3)
    runs: List[Tuple[int, int]] = []
    in_run = False
    start = 0
    for i, e in enumerate(sm):
        if e >= threshold and not in_run:
            in_run = True
            start = i
        elif e < threshold and in_run:
            in_run = False
            runs.append((start, i - 1))
    if in_run:
        runs.append((start, len(sm) - 1))

    # merge runs closer than the refractory window into a single clap
    merged: List[Tuple[int, int]] = []
    for s, e in runs:
        if merged and (s - merged[-1][1]) * block_duration_s < refractory_s:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))

    times = [round(((s + e) / 2) * block_duration_s, 3) for s, e in merged]
    return len(merged), times


class ClapDetector:
    def __init__(self, threshold: int = 700, refractory_s: float = 0.25):
        self.threshold = threshold
        self.refractory_s = refractory_s

    def calibrate(self, ambient: List[float]) -> int:
        """Auto-set `threshold` from an ambient-noise sample; return it."""
        self.threshold = suggest_threshold(ambient)
        return self.threshold

    def analyze(self, energy_per_block: List[float], block_duration_s: float
                ) -> Tuple[int, List[float]]:
        return detect_claps(
            energy_per_block, block_duration_s, self.threshold, self.refractory_s
        )
