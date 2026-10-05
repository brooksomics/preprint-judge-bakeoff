"""Bootstrap uncertainty on MAE. Resample preprints (DOIs) with replacement, B times, fixed seed.

Stdlib only. Percentile method: the 2.5th and 97.5th percentiles of the resampled statistic,
linearly interpolated (statistics.quantiles 'inclusive', the same estimator as numpy's default).
The paired difference test reuses the SAME resamples for both models, so `diff_p` is the share of
worlds in which the model's MAE is at or below the reference model's.
"""

from __future__ import annotations

import math
import random
import statistics as st
from functools import cache

B = 2000
SEED = 0


@cache
def _draws(n: int, seed: int) -> tuple[tuple[int, ...], ...]:
    """B index vectors of length n, drawn with replacement. Cached so paired tests share them."""
    rng = random.Random(seed)
    return tuple(tuple(rng.choices(range(n), k=n)) for _ in range(B))


def _ci(samples: list[float]) -> tuple[float, float]:
    """(2.5th, 97.5th) percentile of the bootstrap distribution."""
    q = st.quantiles(samples, n=40, method="inclusive")
    return q[0], q[-1]


def mae_ci(errs: dict[str, float], seed: int = SEED) -> tuple[float, float]:
    """95% interval on the mean of per-preprint absolute errors."""
    if not errs:
        return math.nan, math.nan
    vals = [errs[d] for d in sorted(errs)]
    return _ci([math.fsum(vals[i] for i in d) / len(d) for d in _draws(len(vals), seed)])


def diff_p(errs: dict[str, float], ref: dict[str, float], seed: int = SEED) -> float:
    """Share of paired resamples where mean(errs) - mean(ref) <= 0, over the DOIs both scored."""
    dois = sorted(set(errs) & set(ref))
    if not dois:
        return math.nan
    delta = [errs[d] - ref[d] for d in dois]
    return sum(math.fsum(delta[i] for i in d) <= 0 for d in _draws(len(dois), seed)) / B
