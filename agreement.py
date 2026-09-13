"""Chance-corrected agreement with the ceiling, stdlib only.

MAE on a squashed score distribution is easy to look good on. These ask about the DECISION:
  kappa_0.5   Cohen's kappa on "score >= 0.5" (model) vs "score >= 0.5" (ceiling), per preprint.
  kappa_top   Cohen's kappa on membership in the top-N shortlist.
  alpha_ord   Krippendorff's alpha, two raters, scores binned to 0.1, distance = squared bin
              difference (the metric the cited implementation calls 'ordinal').
Verdict per category, after judgecal: reliable iff kappa_0.5 >= 0.60 and n >= 8.
"""

from __future__ import annotations

import math
import statistics as st
from collections import Counter, defaultdict

THRESHOLD = 0.5
BIN = 0.1
KAPPA_OK = 0.6
MIN_N = 8


def cohen_kappa(pairs: list[tuple]) -> float:
    """(po - pe) / (1 - pe); 1.0 when both raters are identically constant; NaN when empty."""
    if not pairs:
        return math.nan
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(left[k] * right[k] for k in left.keys() | right.keys()) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def alpha_ordinal(pairs: list[tuple[float, float]]) -> float:
    """Two-rater alpha over 0.1 bins with squared bin distance; 1.0 for perfect agreement."""
    if not pairs:
        return math.nan
    bins = [(round(a / BIN), round(b / BIN)) for a, b in pairs]
    marg = Counter(v for pair in bins for v in pair)  # each pair adds 1 coincidence per direction
    observed = sum(2 * (a - b) ** 2 for a, b in bins)
    cats = list(marg)
    expected = sum(marg[c] * marg[k] * (c - k) ** 2 for c in cats for k in cats if c != k)
    expected /= max(len(bins) * 2 - 1, 1)
    if expected == 0:
        return 1.0 if observed == 0 else math.nan
    return 1 - observed / expected


def kappa_band(kappa: float) -> str:
    """Landis & Koch descriptive band."""
    edges = [(0.0, "worse than chance"), (0.21, "slight"), (0.41, "fair"), (0.61, "moderate")]
    edges += [(0.81, "substantial"), (math.inf, "almost perfect")]
    return next(name for edge, name in edges if kappa < edge)


def decision_pairs(means: dict, ceiling_means: dict) -> list[tuple[int, int]]:
    """(model >= 0.5, ceiling >= 0.5) over the preprints both scored, in DOI order."""
    dois = sorted(set(means) & set(ceiling_means))
    return [(int(means[d] >= THRESHOLD), int(ceiling_means[d] >= THRESHOLD)) for d in dois]


def kappa_top(mine: set, theirs: set, dois: list) -> float:
    """Cohen's kappa on shortlist membership (in the model's top-N vs in the ceiling's)."""
    return cohen_kappa([(int(d in mine), int(d in theirs)) for d in dois])


def verdict(kappa: float, n: int) -> str:
    if n < MIN_N:
        return f"not reliable (n < {MIN_N})"
    return "reliable" if kappa >= KAPPA_OK else "not reliable"


def _means_by_label(rows: list[dict]) -> tuple[dict, dict]:
    """({label: {doi: mean}}, {doi: category-or-'off-lane'}) over scored calls."""
    scores: dict = defaultdict(lambda: defaultdict(list))
    group = {}
    for r in rows:
        if r.get("fit_score") is not None:
            scores[r["label"]][r["doi"]].append(r["fit_score"])
            group[r["doi"]] = "off-lane" if r.get("lane") == "off" else r.get("category", "")
    return {k: {d: st.mean(v) for d, v in dois.items()} for k, dois in scores.items()}, group


def _one(label: str, means: dict, cat: str) -> dict:
    ceiling_means, model_means = means
    pairs = decision_pairs(model_means, ceiling_means)
    common = sorted(set(model_means) & set(ceiling_means))
    return {
        "label": label,
        "category": cat,
        "n": len(pairs),
        "kappa_0.5": cohen_kappa(pairs),
        "alpha_ord": alpha_ordinal([(model_means[d], ceiling_means[d]) for d in common]),
        "verdict": verdict(cohen_kappa(pairs), len(pairs)),
    }


def per_category(rows: list[dict], ceiling: str) -> list[dict]:
    """One row per (label, category) plus an 'all' row; off-lane preprints pooled together."""
    by_label, group = _means_by_label(rows)
    cats = sorted(set(group.values()))
    out = []
    for label, means in by_label.items():
        if label == ceiling:
            continue
        for cat in [*cats, "all"]:
            keep = {d: v for d, v in means.items() if cat == "all" or group[d] == cat}
            ceil = {d: v for d, v in by_label[ceiling].items() if cat == "all" or group[d] == cat}
            out.append(_one(label, (ceil, keep), cat))
    return out
