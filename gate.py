"""Exit-code gate for the re-run: is the production model still fit to ship?

    uv run python gate.py --model tencent/hy3 --min-cov 99 --max-mae-hi 0.12 --min-top10 5 \\
        --max-violations 2

Reads results/results.csv, prints one PASS/FAIL line per check plus a final verdict, exits 0
on PASS and 1 on FAIL. Also fails if the model id is no longer listed by OpenRouter (one GET),
so a deprecated id fails loudly instead of routing somewhere else. Same shape as judgecal's
--min-kappa gate: 0 when the bar is met, 1 when it is not.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path
from typing import NamedTuple

MODELS_URL = "https://openrouter.ai/api/v1/models"


class Thresholds(NamedTuple):
    min_cov: float
    max_mae_hi: float
    min_top10: int
    max_violations: int


def checks(row: dict, t: Thresholds) -> list[tuple[str, bool, str]]:
    """(name, passed, detail) for each threshold against one results.csv row."""
    cov, mae_hi = float(row["cov"]), float(row["mae_hi"])
    top10, viol = int(row["top10"]), int(row["violations"])
    return [
        ("cov", cov >= t.min_cov, f"{cov:.1f} >= {t.min_cov}"),
        ("mae_hi", mae_hi <= t.max_mae_hi, f"{mae_hi:.3f} <= {t.max_mae_hi}"),
        ("top10", top10 >= t.min_top10, f"{top10} >= {t.min_top10}"),
        ("violations", viol <= t.max_violations, f"{viol} <= {t.max_violations}"),
    ]


def live_model_ids() -> set[str]:
    """Model ids OpenRouter lists right now. Response shape verified 2026-09-12: {"data": [..]}."""
    with urllib.request.urlopen(MODELS_URL, timeout=30) as resp:
        return {m["id"] for m in json.loads(resp.read())["data"]}


def _args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", required=True)
    ap.add_argument("--csv", type=Path, default=Path("results/results.csv"))
    ap.add_argument("--min-cov", type=float, default=99.0)
    ap.add_argument("--max-mae-hi", type=float, default=0.12)
    ap.add_argument("--min-top10", type=int, default=5)
    ap.add_argument("--max-violations", type=int, default=2)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = _args(argv)
    rows = {r["label"]: r for r in csv.DictReader(a.csv.open())}
    if a.model not in rows:
        print(f"FAIL  {a.model} has no row in {a.csv}\nFAIL")
        return 1
    t = Thresholds(a.min_cov, a.max_mae_hi, a.min_top10, a.max_violations)
    listed = a.model in live_model_ids()
    results = checks(rows[a.model], t) + [
        ("listed", listed, "id listed by OpenRouter" if listed else "id not listed by OpenRouter")
    ]
    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name:<11} {detail}")
    verdict = all(passed for _, passed, _ in results)
    print("PASS" if verdict else "FAIL")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
