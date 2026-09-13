"""Grade results.jsonl against the ceiling: metrics table (markdown + CSV) and two figures.

Metrics, per model config:
  cov         % of calls that returned a parseable 0-1 score (timeouts, bad JSON count against)
  strict      % of those whose whole body was clean JSON, nothing before or after it
  violations  CALLS on an off-lane preprint scored >= 0.5. Counts calls, not preprints: a
              preprint misjudged on all 3 repeats contributes 3.
  sigma       mean over preprints of the std dev across the 3 repeats (repeatability)
  mae         mean over preprints of |model mean - ceiling mean| (agreement with the ceiling)
  mae_lo/hi   95% bootstrap interval on mae: preprints resampled with replacement (bootstrap.py)
  mae_diff_p  paired bootstrap: share of resamples where this model's MAE <= the best usable
              model's (lowest MAE at >= USABLE_COV coverage). 1.0 for the reference itself.
  top10       of the ceiling's 10 highest-scoring preprints, how many are in the model's own
              top 10. The decision the triage step actually makes, which a compressed score
              distribution can hide from MAE.
  latency_s   mean wall-clock seconds per call
  cost_usd    mean OpenRouter-reported cost per call that returned
"""

from __future__ import annotations

import argparse
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import bootstrap

CEILING = "anthropic/claude-sonnet-5"
COLUMNS = (
    "label",
    "cov",
    "strict",
    "violations",
    "sigma",
    "mae",
    "mae_lo",
    "mae_hi",
    "mae_diff_p",
    "top10",
    "latency_s",
    "cost_usd",
    "n_calls",
)
VIOLATION_AT = 0.5
SHORTLIST = 10
USABLE_COV = 99.0


def load_rows(results: Path, preprints: Path) -> list[dict]:
    lane = {p["doi"]: p["lane"] for p in json.loads(preprints.read_text())}
    rows = [json.loads(line) for line in results.read_text().splitlines() if line.strip()]
    return [{**r, "lane": lane.get(r["doi"], r.get("lane", "in"))} for r in rows]


def _scores(runs: list[dict]) -> list[float]:
    return [r["fit_score"] for r in runs if r.get("fit_score") is not None]


def _item_means(by_item: dict) -> dict[str, float]:
    return {doi: st.mean(s) for doi, runs in by_item.items() if (s := _scores(runs))}


def shortlist(means: dict[str, float], n: int) -> set[str]:
    """The n highest-scoring preprints; DOI order breaks ties so it is deterministic."""
    return {d for d, _ in sorted(means.items(), key=lambda kv: (-kv[1], kv[0]))[:n]}


def _pct(hits: int, total: int) -> float:
    return 100 * hits / total if total else math.nan


def _agreement(means: dict, ceiling_means: dict) -> dict:
    """MAE with its bootstrap interval, top-N overlap, and the per-preprint errors (for pairing)."""
    errs = {d: abs(m - ceiling_means[d]) for d, m in means.items() if d in ceiling_means}
    lo, hi = bootstrap.mae_ci(errs)
    top = shortlist(means, SHORTLIST) & shortlist(ceiling_means, SHORTLIST)
    mae = st.mean(errs.values()) if errs else math.nan
    return {"mae": mae, "mae_lo": lo, "mae_hi": hi, "top10": len(top), "_errs": errs}


def _one(by_item: dict, ceiling_means: dict) -> dict:
    runs = [r for rs in by_item.values() for r in rs]
    scored = [r for r in runs if r.get("fit_score") is not None]
    sig = [st.stdev(s) for rs in by_item.values() if len(s := _scores(rs)) >= 2]
    costs = [c for r in runs if (c := r.get("cost_usd")) is not None]
    off = [r for r in scored if r["lane"] == "off"]
    return {
        "cov": 100 * len(scored) / len(runs),
        "strict": _pct(sum(bool(r.get("strict_json")) for r in scored), len(scored)),
        "violations": sum(1 for r in off if r["fit_score"] >= VIOLATION_AT),
        "sigma": st.mean(sig) if sig else math.nan,
        **_agreement(_item_means(by_item), ceiling_means),
        "latency_s": st.mean([r.get("latency_s", 0.0) for r in runs]),
        "cost_usd": st.mean(costs) if costs else math.nan,
        "n_calls": len(runs),
    }


def best_usable(m: dict, ceiling: str) -> str:
    """Reference for the paired test: lowest MAE among non-ceiling labels at >= USABLE_COV
    coverage; falls back to the lowest MAE overall, then to the ceiling itself."""
    cands = [k for k, r in m.items() if k != ceiling and not math.isnan(r["mae"])]
    usable = [k for k in cands if m[k]["cov"] >= USABLE_COV] or cands or [ceiling]
    return min(usable, key=lambda k: m[k]["mae"])


def metrics(rows: list[dict], ceiling: str = CEILING) -> dict[str, dict]:
    """Per-label metrics, ordered best agreement first (NaN MAE, i.e. no ceiling overlap, last)."""
    by_label: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_label[r["label"]][r["doi"]].append(r)
    ceiling_means = _item_means(by_label[ceiling])
    m = {label: _one(items, ceiling_means) for label, items in by_label.items()}
    ref = m[best_usable(m, ceiling)]["_errs"]
    for r in m.values():
        r["mae_diff_p"] = bootstrap.diff_p(r.pop("_errs"), ref)
    return dict(sorted(m.items(), key=lambda kv: (math.isnan(kv[1]["mae"]), kv[1]["mae"])))


def main() -> None:  # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=Path("data/results.jsonl"))
    ap.add_argument("--preprints", type=Path, default=Path("data/preprints.json"))
    ap.add_argument("--out", type=Path, default=Path("results"))
    ap.add_argument("--ceiling", default=CEILING)
    a = ap.parse_args()
    import figures
    import report

    rows = load_rows(a.results, a.preprints)
    m = metrics(rows, a.ceiling)
    report.write_tables(m, a.out)
    figures.plot_all(m, a.out, a.ceiling)
    if Path("README.md").exists():
        report.sync_readme(Path("README.md"), (a.out / "results.md").read_text())
    print((a.out / "results.md").read_text())
    report.print_details(rows)


if __name__ == "__main__":
    main()
