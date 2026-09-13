"""Zero-LLM control: tf-idf cosine between profile.md and each preprint's title + abstract.

Stdlib only. tf = 1 + log(count), idf = log((N + 1) / (df + 1)) over the N preprints, cosine to the
profile, then min-max to [0, 1]. Its scale is not a fit_score, so MAE against the ceiling is marked
n/a in the table; top-10 overlap and Spearman are the comparable columns. Every LLM row should
beat this for free.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

LABEL = "baseline:tfidf"
TOKEN = re.compile(r"[a-z][a-z0-9-]{2,}")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def idf(docs: list[list[str]]) -> dict[str, float]:
    df = Counter(t for d in docs for t in set(d))
    n = len(docs)
    return {t: math.log((n + 1) / (c + 1)) for t, c in df.items()}


def vector(tokens: list[str], weights: dict[str, float]) -> dict[str, float]:
    tf = Counter(t for t in tokens if t in weights)
    return {t: (1 + math.log(c)) * weights[t] for t, c in tf.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(a[t] * b[t] for t in a.keys() & b.keys())
    norm = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return dot / norm if norm else 0.0


def minmax(xs: dict[str, float]) -> dict[str, float]:
    lo, hi = min(xs.values()), max(xs.values())
    return {k: (v - lo) / (hi - lo) if hi > lo else 0.0 for k, v in xs.items()}


def scores(preprints: list[dict], profile: str) -> dict[str, float]:
    docs = [tokenize(p["title"] + " " + p["abstract"]) for p in preprints]
    weights = idf(docs)
    query = vector(tokenize(profile), weights)
    sims = {
        p["doi"]: cosine(vector(d, weights), query) for p, d in zip(preprints, docs, strict=True)
    }
    return minmax(sims)


def rows(preprints: Path, profile: Path) -> list[dict]:
    """One synthetic, free, always-parseable call per preprint, shaped like a harness row."""
    items = json.loads(preprints.read_text())
    fit = scores(items, profile.read_text())
    return [
        {
            "label": LABEL,
            "doi": p["doi"],
            "run_idx": 0,
            "fit_score": fit[p["doi"]],
            "lane": p["lane"],
            "title": p["title"],
            "category": p.get("category", ""),
            "latency_s": 0.0,
            "cost_usd": 0.0,
            "strict_json": True,
        }
        for p in items
    ]
