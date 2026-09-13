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
  spearman    rank correlation between the model's and the ceiling's per-preprint means
  kappa_0.5   Cohen's kappa on the decision score >= 0.5, model vs ceiling (agreement.py)
  alpha_ord   Krippendorff's alpha over 0.1 bins, squared bin distance, model vs ceiling
  kappa_top10 Cohen's kappa on membership in the top-10 shortlist
  top10       of the ceiling's 10 highest-scoring preprints, how many are in the model's own
              top 10. The decision the triage step actually makes, which a compressed score
              distribution can hide from MAE.
  latency_s   mean wall-clock seconds per call
  cost_usd    mean OpenRouter-reported cost per call that returned
  derived     True for rows computed from other rows (baseline:, ens:), never the reference

--top-disagreement N also writes results/disagreement.md (see disagreement.py).
"""

from __future__ import annotations

import argparse
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import agreement
import bootstrap
import rankstats

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
    "spearman",
    "kappa_0.5",
    "alpha_ord",
    "kappa_top10",
    "top10",
    "latency_s",
    "cost_usd",
    "n_calls",
    "derived",
)
VIOLATION_AT = 0.5
SHORTLIST = 10
USABLE_COV = 99.0
DERIVED = ("baseline:", "ens:")  # rows computed from other rows, not API calls
UNSCALED = ("baseline:",)  # not a fit score: MAE against the ceiling is meaningless


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


def _agreement(means: dict, ceiling_means: dict) -> dict:
    """MAE with its bootstrap interval, rank/decision agreement, and per-preprint errors."""
    dois = sorted(d for d in means if d in ceiling_means)
    errs = {d: abs(means[d] - ceiling_means[d]) for d in dois}
    lo, hi = bootstrap.mae_ci(errs)
    mine, theirs = shortlist(means, SHORTLIST), shortlist(ceiling_means, SHORTLIST)
    pairs = agreement.decision_pairs(means, ceiling_means)
    return {
        "mae": st.mean(errs.values()) if errs else math.nan,
        "mae_lo": lo,
        "mae_hi": hi,
        "spearman": rankstats.spearman([means[d] for d in dois], [ceiling_means[d] for d in dois]),
        "kappa_0.5": agreement.cohen_kappa(pairs),
        "alpha_ord": agreement.alpha_ordinal([(means[d], ceiling_means[d]) for d in dois]),
        "kappa_top10": agreement.kappa_top(mine, theirs, dois),
        "top10": len(mine & theirs),
        "_errs": errs,
    }


def _one(by_item: dict, ceiling_means: dict) -> dict:
    runs = [r for rs in by_item.values() for r in rs]
    scored = [r for r in runs if r.get("fit_score") is not None]
    sig = [st.stdev(s) for rs in by_item.values() if len(s := _scores(rs)) >= 2]
    costs = [c for r in runs if (c := r.get("cost_usd")) is not None]
    off = [r for r in scored if r["lane"] == "off"]
    return {
        "cov": 100 * len(scored) / len(runs),
        "strict": 100 * sum(bool(r.get("strict_json")) for r in scored) / len(scored)
        if scored
        else math.nan,
        "violations": sum(1 for r in off if r["fit_score"] >= VIOLATION_AT),
        "sigma": st.mean(sig) if sig else math.nan,
        **_agreement(_item_means(by_item), ceiling_means),
        "latency_s": st.mean([r.get("latency_s", 0.0) for r in runs]),
        "cost_usd": st.mean(costs) if costs else math.nan,
        "n_calls": len(runs),
    }


def best_usable(m: dict, ceiling: str) -> str:
    """Reference for the paired test: lowest MAE among single (non-derived, non-ceiling) models
    at >= USABLE_COV coverage; falls back to the lowest MAE overall, then to the ceiling."""
    cands = [k for k, r in m.items() if k != ceiling and not (math.isnan(r["mae"]) or r["derived"])]
    usable = [k for k in cands if m[k]["cov"] >= USABLE_COV] or cands or [ceiling]
    return min(usable, key=lambda k: m[k]["mae"])


def metrics(rows: list[dict], ceiling: str = CEILING) -> dict[str, dict]:
    """Per-label metrics, ordered best agreement first (NaN MAE, i.e. no ceiling overlap, last)."""
    by_label: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_label[r["label"]][r["doi"]].append(r)
    ceiling_means = _item_means(by_label[ceiling])
    m = {label: _one(items, ceiling_means) for label, items in by_label.items()}
    for k, r in m.items():
        r["derived"] = k.startswith(DERIVED)
        if k.startswith(UNSCALED):
            r.update(mae=math.nan, mae_lo=math.nan, mae_hi=math.nan, alpha_ord=math.nan)
            r["kappa_0.5"] = math.nan
    ref = m[best_usable(m, ceiling)]["_errs"]
    for r in m.values():
        r["mae_diff_p"] = bootstrap.diff_p(r.pop("_errs"), ref)
    return dict(sorted(m.items(), key=lambda kv: (math.isnan(kv[1]["mae"]), kv[1]["mae"])))


def _args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=Path("data/results.jsonl"))
    ap.add_argument("--preprints", type=Path, default=Path("data/preprints.json"))
    ap.add_argument("--profile", type=Path, default=Path("profile.md"))
    ap.add_argument("--out", type=Path, default=Path("results"))
    ap.add_argument("--ceiling", default=CEILING)
    ap.add_argument("--top-disagreement", type=int, default=10, help="rows in disagreement.md")
    return ap.parse_args()


def main() -> None:  # pragma: no cover
    import baseline
    import disagreement
    import ensembles
    import figures
    import report

    a = _args()
    rows = load_rows(a.results, a.preprints) + baseline.rows(a.preprints, a.profile)
    rows += ensembles.all_rows(rows)
    m = metrics(rows, a.ceiling)
    report.write_tables(m, a.out)
    figures.plot_all(m, a.out, a.ceiling)
    report.sync_readme(Path("README.md"), (a.out / "results.md").read_text())
    spec = disagreement.Spec(a.ceiling, a.top_disagreement)
    (a.out / "disagreement.md").write_text(disagreement.markdown(rows, m, spec))
    report.write_agreement(
        agreement.per_category(rows, a.ceiling), a.out / "agreement_by_category.md"
    )
    report.print_details(rows, a.out)


if __name__ == "__main__":
    main()
