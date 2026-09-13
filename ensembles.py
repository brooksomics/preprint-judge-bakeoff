"""Synthetic ensemble rows: the median of k cheap models' scores, as a derived challenger.

Compound judges are the thesis of frameworks like haizelabs/verdict ("instead of a single LLM
call ... aggregation"). Here the cheapest version: per preprint, the median of each component's
mean score; cost is the components' summed cost, latency the slowest component, and the row is
unscored wherever any component failed (all-or-nothing coverage). Only the pre-registered
combinations below are reported. They were chosen by the rules in the comments BEFORE any
ensemble was scored; there was no search over combinations, because a search over the same 90
preprints the table is scored on would be optimistic by construction.
"""

from __future__ import annotations

import statistics as st
from collections import defaultdict

ENSEMBLES = [
    # best MAE + steadiest sigma + best top-10 among usable single models
    ("tencent/hy3", "google/gemini-3.5-flash-lite", "deepseek/deepseek-v4.1-flash"),
    # the three cheapest usable models by $/call
    ("tencent/hy3", "xiaomi/mimo-v2.5", "inception/mercury-2.5"),
    # the three lowest-MAE usable models from three different labs
    ("tencent/hy3", "deepseek/deepseek-v4-flash-0731@medium", "xiaomi/mimo-v2.5"),
]


def label(components: tuple[str, ...]) -> str:
    return "ens:" + "+".join(c.split("/", 1)[-1] for c in components)


def _per_item(rows: list[dict], components: tuple[str, ...]) -> tuple[dict, dict]:
    """({doi: {label: {"score": mean | None, "cost": mean, "latency": mean}}}, {doi: meta})."""
    runs: dict = defaultdict(lambda: defaultdict(list))
    meta = {}
    for r in rows:
        if r["label"] in components:
            runs[r["doi"]][r["label"]].append(r)
            meta[r["doi"]] = {k: r.get(k) for k in ("lane", "title", "category")}
    stats = {}
    for doi, by_label in runs.items():
        stats[doi] = {}
        for lab, rs in by_label.items():
            scores = [x["fit_score"] for x in rs if x.get("fit_score") is not None]
            stats[doi][lab] = {
                "score": st.mean(scores) if scores else None,
                "cost": st.mean(x.get("cost_usd") or 0.0 for x in rs),
                "latency": st.mean(x.get("latency_s") or 0.0 for x in rs),
            }
    return stats, meta


def _row(doi: str, parts: list[dict], components: tuple[str, ...]) -> dict:
    scores = [p["score"] for p in parts]
    score = st.median(scores) if all(s is not None for s in scores) else None
    return {
        "label": label(components),
        "doi": doi,
        "run_idx": 0,
        "fit_score": score,
        "cost_usd": sum(p["cost"] for p in parts),
        "latency_s": max(p["latency"] for p in parts),
        "strict_json": score is not None,
    }


def rows(rows: list[dict], components: tuple[str, ...]) -> list[dict]:
    """One synthetic call per preprint that every component saw."""
    stats, meta = _per_item(rows, components)
    out = []
    for doi, by_label in stats.items():
        parts = [by_label[c] for c in components if c in by_label]
        if len(parts) == len(components):
            out.append({**_row(doi, parts, components), **meta[doi]})
    return out


def all_rows(rows_in: list[dict]) -> list[dict]:
    """Rows for every pre-registered ensemble whose components all appear in the data."""
    present = {r["label"] for r in rows_in}
    return [r for combo in ENSEMBLES if set(combo) <= present for r in rows(rows_in, combo)]
