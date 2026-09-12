"""Grade results.jsonl against the ceiling: metrics table (markdown + CSV) and two figures.

Metrics, per model config:
  cov         % of calls that returned a parseable 0-1 score (timeouts, bad JSON count against)
  strict      % of those whose whole body was clean JSON, nothing before or after it
  violations  CALLS on an off-lane preprint scored >= 0.5. Counts calls, not preprints: a
              preprint misjudged on all 3 repeats contributes 3.
  sigma       mean over preprints of the std dev across the 3 repeats (repeatability)
  mae         mean over preprints of |model mean - ceiling mean| (agreement with the ceiling)
  top10       of the ceiling's 10 highest-scoring preprints, how many are in the model's own
              top 10. The decision the triage step actually makes, which a compressed score
              distribution can hide from MAE.
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
    "top10",
    "latency_s",
    "cost_usd",
    "n_calls",
)
VIOLATION_AT = 0.5
SHORTLIST = 10


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


def _agreement(means: dict, ceiling_means: dict) -> tuple[float, int]:
    """(MAE, top-N overlap) against the ceiling's per-preprint means."""
    maes = [abs(m - ceiling_means[d]) for d, m in means.items() if d in ceiling_means]
    top = shortlist(means, SHORTLIST) & shortlist(ceiling_means, SHORTLIST)
    return (st.mean(maes) if maes else math.nan), len(top)


def _one(by_item: dict, ceiling_means: dict) -> dict:
    runs = [r for rs in by_item.values() for r in rs]
    scored = [r for r in runs if r.get("fit_score") is not None]
    means = _item_means(by_item)
    mae, top = _agreement(means, ceiling_means)
    sig = [st.stdev(s) for rs in by_item.values() if len(s := _scores(rs)) >= 2]
    costs = [c for r in runs if (c := r.get("cost_usd")) is not None]
    off = [r for r in scored if r["lane"] == "off"]
    return {
        "cov": 100 * len(scored) / len(runs),
        "strict": _pct(sum(bool(r.get("strict_json")) for r in scored), len(scored)),
        "violations": sum(1 for r in off if r["fit_score"] >= VIOLATION_AT),
        "sigma": st.mean(sig) if sig else math.nan,
        "mae": mae,
        "top10": top,
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
    cols = "| model | cov% | strict% | wrong-field | sigma | MAE vs ceiling |"
    md = [
        f"{cols} top-{SHORTLIST} | latency s | $/call |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for k, r in m.items():
        md.append(
            f"| {k} | {r['cov']:.1f} | {r['strict']:.1f} | {r['violations']} | {r['sigma']:.3f} "
            f"| {r['mae']:.3f} | {r['top10']}/{SHORTLIST} | {r['latency_s']:.2f} "
            f"| {r['cost_usd']:.5f} |"
        )
    path.write_text("\n".join(md) + "\n")


def write_tables(m: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_csv(m, out / "results.csv")
    write_md(m, out / "results.md")


def provider_detail(rows: list[dict], floor: float = 100.0) -> list[str]:
    """Coverage per (label, provider). The same model id routes to several providers on
    OpenRouter and they do not all honor the same parameters, so a coverage hole is often one
    provider rather than one model."""
    by: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        by[(r["label"], r.get("provider") or "none")].append(r)
    out = []
    for (label, prov), rs in sorted(by.items()):
        cov = 100 * sum(r.get("fit_score") is not None for r in rs) / len(rs)
        rtok = [t for r in rs if (t := r.get("reasoning_tokens")) is not None]
        thinking = f", mean {st.mean(rtok):.0f} reasoning tok" if rtok and st.mean(rtok) else ""
        if cov < floor:
            out.append(f"{label} via {prov}: {cov:.1f}% of {len(rs)} calls{thinking}")
    return out


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
    print("\nProviders that did not return a score on every call:")
    print("\n".join("  " + line for line in provider_detail(rows)) or "  none")


if __name__ == "__main__":
    main()
