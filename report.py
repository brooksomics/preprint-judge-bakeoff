"""Write the results tables (CSV + markdown), the detail printouts, and sync the README block."""

from __future__ import annotations

import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

from analyze import COLUMNS, DERIVED, SHORTLIST, VIOLATION_AT

MARK_START, MARK_END = "<!-- RESULTS:START -->", "<!-- RESULTS:END -->"


def write_csv(m: dict, path: Path) -> None:
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for k, r in m.items():
            w.writerow(
                [k] + [round(r[c], 5) if isinstance(r[c], float) else r[c] for c in COLUMNS[1:]]
            )


def _num(v: float, fmt: str) -> str:
    return "n/a" if math.isnan(v) else format(v, fmt)


def _mae_cell(k: str, r: dict) -> str:
    if k.startswith(DERIVED):
        return "n/a | n/a"
    return f"{r['mae']:.3f} [{r['mae_lo']:.3f}, {r['mae_hi']:.3f}] | {r['mae_diff_p']:.2f}"


def write_md(m: dict, path: Path) -> None:
    cols = "| model | cov% | strict% | wrong-field | sigma | MAE vs ceiling [95% CI] | P(<= best) |"
    md = [
        f"{cols} rho | top-{SHORTLIST} | latency s | $/call |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for k, r in m.items():
        md.append(
            f"| {k} | {r['cov']:.1f} | {r['strict']:.1f} | {r['violations']} "
            f"| {_num(r['sigma'], '.3f')} | {_mae_cell(k, r)} | {r['spearman']:.2f} "
            f"| {r['top10']}/{SHORTLIST} | {r['latency_s']:.2f} | {r['cost_usd']:.5f} |"
        )
    path.write_text("\n".join(md) + "\n")


def write_tables(m: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    write_csv(m, out / "results.csv")
    write_md(m, out / "results.md")


def sync_readme(readme: Path, table_md: str) -> None:
    """Replace the markdown table between the RESULTS markers with table_md; prose stays."""
    if not readme.exists():
        return
    text = readme.read_text()
    head, rest = text.split(MARK_START, 1)
    block, tail = rest.split(MARK_END, 1)
    lines = block.splitlines()
    idx = [i for i, ln in enumerate(lines) if ln.startswith("|")]
    lines[idx[0] : idx[-1] + 1] = table_md.strip().splitlines()
    readme.write_text(head + MARK_START + "\n".join(lines) + "\n" + MARK_END + tail)


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


def print_details(rows: list[dict], out: Path) -> None:
    print((out / "results.md").read_text())
    print("Wrong-field detail (off-lane scored >= 0.5):")
    print("\n".join("  " + line for line in violation_detail(rows)) or "  none")
    print("\nProviders that did not return a score on every call:")
    print("\n".join("  " + line for line in provider_detail(rows)) or "  none")
