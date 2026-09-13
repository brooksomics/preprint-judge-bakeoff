"""Bias probes on a single-item scorer.

Length: per model, Spearman between abstract word count and the per-preprint mean score. A judge
that rewards long abstracts shows a positive rho; what matters is the gap from the ceiling's own
rho, so models are flagged when |rho - rho_ceiling| > FLAG_AT.

Not probed, and why: position bias (one item per call, nothing to reorder), self-preference (no
model judges its own output), and the padded-twin verbosity design (pairwise; this judge never
sees two candidates).
"""

from __future__ import annotations

import math
import statistics as st

import rankstats

FLAG_AT = 0.2


def len_rho(by_item: dict[str, list[dict]]) -> float:
    """Spearman(abstract words, mean score) over preprints with both a score and a length."""
    pts = []
    for runs in by_item.values():
        scores = [r["fit_score"] for r in runs if r.get("fit_score") is not None]
        if scores and runs[0].get("n_words"):
            pts.append((st.mean(scores), runs[0]["n_words"]))
    return rankstats.spearman([p[0] for p in pts], [p[1] for p in pts])


def flagged(m: dict, ceiling: str) -> list[str]:
    """Labels whose length correlation departs from the ceiling's by more than FLAG_AT."""
    ref = m[ceiling]["len_rho"]
    return [
        k
        for k, r in m.items()
        if k != ceiling and not math.isnan(r["len_rho"]) and abs(r["len_rho"] - ref) > FLAG_AT
    ]
