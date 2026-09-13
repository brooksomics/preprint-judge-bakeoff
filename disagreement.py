"""Disagreement audit: which preprints do the usable models split on most, and least.

For each preprint, take every usable model's mean score (>= USABLE_COV coverage, ceiling excluded)
and rank preprints by the population std dev of those means, highest first. The items at the top
are the ones a human should read; the mirror list (lowest spread) shows what everyone agrees on.
"""

from __future__ import annotations

import statistics as st
from collections import defaultdict
from typing import NamedTuple

from analyze import USABLE_COV


class Spec(NamedTuple):
    ceiling: str
    n: int = 10


def usable_labels(m: dict, ceiling: str) -> list[str]:
    return sorted(k for k, r in m.items() if k != ceiling and r["cov"] >= USABLE_COV)


def _means(rows: list[dict]) -> tuple[dict, dict]:
    """({doi: {label: mean score}}, {doi: (title, category, lane)}) over scored calls."""
    by: dict = defaultdict(lambda: defaultdict(list))
    meta = {}
    for r in rows:
        if r.get("fit_score") is not None:
            by[r["doi"]][r["label"]].append(r["fit_score"])
            meta[r["doi"]] = (r.get("title", r["doi"]), r.get("category", ""), r.get("lane", ""))
    return {d: {k: st.mean(v) for k, v in labs.items()} for d, labs in by.items()}, meta


def _item(doi: str, scores: dict[str, float], ceiling: float | None) -> dict:
    lo, hi = min(scores, key=scores.get), max(scores, key=scores.get)
    return {
        "doi": doi,
        "sd": st.pstdev(scores.values()),
        "ceiling": ceiling,
        "lo": scores[lo],
        "lo_model": lo,
        "hi": scores[hi],
        "hi_model": hi,
    }


def rank(rows: list[dict], m: dict, spec: Spec) -> tuple[list[dict], list[dict]]:
    """(top-n most disputed, top-n most agreed) items, each dict carrying title/category/lane."""
    labels = usable_labels(m, spec.ceiling)
    means, meta = _means(rows)
    items = []
    for doi, per_label in means.items():
        scores = {k: per_label[k] for k in labels if k in per_label}
        if len(scores) >= 2:
            title, category, lane = meta[doi]
            item = _item(doi, scores, per_label.get(spec.ceiling))
            items.append({**item, "title": title, "category": category, "lane": lane})
    items.sort(key=lambda r: (-r["sd"], r["doi"]))
    return items[: spec.n], sorted(items, key=lambda r: (r["sd"], r["doi"]))[: spec.n]


def _table(items: list[dict]) -> list[str]:
    head = ["| # | sd | ceiling | min (model) | max (model) | category / lane | title | doi |"]
    head.append("|--:|--:|--:|---|---|---|---|---|")
    for i, r in enumerate(items, 1):
        ceiling = "n/a" if r["ceiling"] is None else f"{r['ceiling']:.2f}"
        head.append(
            f"| {i} | {r['sd']:.3f} | {ceiling} | {r['lo']:.2f} ({r['lo_model']}) "
            f"| {r['hi']:.2f} ({r['hi_model']}) | {r['category']} / {r['lane']} "
            f"| {r['title']} | {r['doi']} |"
        )
    return head


def markdown(rows: list[dict], m: dict, spec: Spec) -> str:
    top, bottom = rank(rows, m, spec)
    n_models = len(usable_labels(m, spec.ceiling))
    parts = [
        f"# Where the {n_models} usable models disagree",
        "",
        f"Population std dev of the per-model mean score, over the {n_models} usable models "
        f"(>= {USABLE_COV:.0f}% coverage, ceiling excluded). `ceiling` is the ceiling's own mean.",
        "",
        f"## Top {len(top)} most disputed",
        "",
        *_table(top),
        "",
        f"## Top {len(bottom)} most agreed",
        "",
        *_table(bottom),
        "",
    ]
    return "\n".join(parts)
