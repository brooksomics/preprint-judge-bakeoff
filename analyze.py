"""Grade results.jsonl against the ceiling: metrics table (markdown + CSV) and two figures.

Metrics, per model config:
  cov         % of calls that returned a parseable 0-1 score (timeouts, bad JSON count against)
  strict      % of those whose whole body was clean JSON, nothing before or after it
  violations  off-lane preprints scored >= 0.5 (a "wrong-field" call)
  sigma       mean over preprints of the std dev across the 3 repeats (repeatability)
  mae         mean over preprints of |model mean - ceiling mean| (agreement with the ceiling)
  latency_s   mean wall-clock seconds per call
  cost_usd    mean OpenRouter-reported cost per call that returned
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

CEILING = "anthropic/claude-sonnet-5"
COLUMNS = (
    "label",
    "cov",
    "strict",
    "violations",
    "sigma",
    "mae",
    "latency_s",
    "cost_usd",
    "n_calls",
)
VIOLATION_AT = 0.5


def load_rows(results: Path, preprints: Path) -> list[dict]:
    lane = {p["doi"]: p["lane"] for p in json.loads(preprints.read_text())}
    rows = [json.loads(line) for line in results.read_text().splitlines() if line.strip()]
    return [{**r, "lane": lane.get(r["doi"], r.get("lane", "in"))} for r in rows]


def _scores(runs: list[dict]) -> list[float]:
    return [r["fit_score"] for r in runs if r.get("fit_score") is not None]


def _item_means(by_item: dict) -> dict[str, float]:
    return {doi: st.mean(s) for doi, runs in by_item.items() if (s := _scores(runs))}


def _one(by_item: dict, ceiling_means: dict) -> dict:
    runs = [r for rs in by_item.values() for r in rs]
    scored = [r for r in runs if r.get("fit_score") is not None]
    means = _item_means(by_item)
    maes = [abs(m - ceiling_means[d]) for d, m in means.items() if d in ceiling_means]
    sig = [st.stdev(s) for rs in by_item.values() if len(s := _scores(rs)) >= 2]
    costs = [c for r in runs if (c := r.get("cost_usd")) is not None]
    return {
        "cov": 100 * len(scored) / len(runs),
        "strict": 100 * sum(bool(r.get("strict_json")) for r in scored) / len(scored)
        if scored
        else math.nan,
        "violations": sum(
            1 for r in scored if r["lane"] == "off" and r["fit_score"] >= VIOLATION_AT
        ),
        "sigma": st.mean(sig) if sig else math.nan,
        "mae": st.mean(maes) if maes else math.nan,
        "latency_s": st.mean([r.get("latency_s", 0.0) for r in runs]),
        "cost_usd": st.mean(costs) if costs else math.nan,
        "n_calls": len(runs),
    }


def metrics(rows: list[dict], ceiling: str = CEILING) -> dict[str, dict]:
    """Per-label metrics, ordered best agreement first (NaN MAE, i.e. no ceiling overlap, last)."""
    by_label: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_label[r["label"]][r["doi"]].append(r)
    ceiling_means = _item_means(by_label[ceiling])
    m = {label: _one(items, ceiling_means) for label, items in by_label.items()}
    return dict(sorted(m.items(), key=lambda kv: (math.isnan(kv[1]["mae"]), kv[1]["mae"])))


def write_csv(m: dict, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for k, r in m.items():
            w.writerow(
                [k] + [round(r[c], 5) if isinstance(r[c], float) else r[c] for c in COLUMNS[1:]]
            )


def write_md(m: dict, path: Path) -> None:
    md = ["| model | cov% | strict% | wrong-field | sigma | MAE vs ceiling | latency s | $/call |"]
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k, r in m.items():
        md.append(
            f"| {k} | {r['cov']:.1f} | {r['strict']:.1f} | {r['violations']} | {r['sigma']:.3f} "
            f"| {r['mae']:.3f} | {r['latency_s']:.2f} | {r['cost_usd']:.5f} |"
        )
    path.write_text("\n".join(md) + "\n")


def write_tables(m: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_csv(m, out / "results.csv")
    write_md(m, out / "results.md")


def violation_detail(rows: list[dict]) -> list[str]:
    bad = [r for r in rows if r["lane"] == "off" and (r.get("fit_score") or 0) >= VIOLATION_AT]
    return [
        f"{r['label']}: {r.get('title', r['doi'])[:70]} [{r['category']}] -> {r['fit_score']}"
        for r in bad
    ]


def main() -> None:  # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path, default=Path("data/results.jsonl"))
    ap.add_argument("--preprints", type=Path, default=Path("data/preprints.json"))
    ap.add_argument("--out", type=Path, default=Path("results"))
    ap.add_argument("--ceiling", default=CEILING)
    a = ap.parse_args()
    rows = load_rows(a.results, a.preprints)
    m = metrics(rows, a.ceiling)
    write_tables(m, a.out)
    import figures

    figures.plot_all(m, a.out, a.ceiling)
    print((a.out / "results.md").read_text())
    print("Wrong-field detail (off-lane scored >= 0.5):")
    print("\n".join("  " + line for line in violation_detail(rows)) or "  none")


if __name__ == "__main__":
    main()
