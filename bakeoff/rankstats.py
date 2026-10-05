"""Rank statistics, stdlib only. Spearman = Pearson correlation of average ranks."""

from __future__ import annotations

import math
import statistics as st


def ranks(xs: list[float]) -> list[float]:
    """1-based ranks; ties get the average of the positions they span."""
    order = sorted(range(len(xs)), key=xs.__getitem__)
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in order[i : j + 1]:
            out[k] = (i + j) / 2 + 1
        i = j + 1
    return out


def spearman(x: list[float], y: list[float]) -> float:
    """Spearman rho; NaN with fewer than 3 pairs or a constant side."""
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return math.nan
    return st.correlation(ranks(x), ranks(y))
