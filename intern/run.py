"""Biweekly run: fetch, dedupe against seen DOIs, score once with the production model, email.

    uv run python -m intern --dry-run     # render the digest to stdout, send nothing
    uv run python -m intern               # what launchd runs every Thursday; sends only if due

launchd has no biweekly primitive, so the plist fires weekly and `due()` refuses to send when
the last digest went out under MIN_GAP_DAYS ago. Budget guard: abort before scoring if the
estimated cost exceeds BUDGET_USD, and again after if the measured cost did.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import fetch_preprints
import harness
from intern import credentials, mailer

STATE_DIR = Path("~/.preprint-judge").expanduser()
STATE = (STATE_DIR / "seen.json", STATE_DIR / "intern.log")
MODEL = ("tencent/hy3", "off")  # the gate-approved production judge, reasoning off
BUDGET_USD = 0.10
EST_PER_CALL = 0.0001  # generous: hy3 measured $0.00006
MIN_GAP_DAYS = 13
WORKERS = 8


def load_seen(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"dois": [], "last_sent": None}


def fetch_recent(days: int, cap: int) -> list[dict]:
    """Every in-lane preprint from the last `days` days (no off-lane: this is production)."""
    window = fetch_preprints.Window(date.today() - timedelta(days=days), date.today())
    rows = [
        r
        for c in sorted(fetch_preprints.IN_LANE)
        for r in fetch_preprints.fetch_category(c, window, cap)
    ]
    return [{**fetch_preprints.slim(r), "lane": "in"} for r in rows]


def unseen(items: list[dict], seen: dict) -> list[dict]:
    done = set(seen.get("dois", []))
    return [it for it in items if it["doi"] not in done]


def due(seen: dict, today: date) -> bool:
    last = seen.get("last_sent")
    return last is None or (today - date.fromisoformat(last)).days >= MIN_GAP_DAYS


def score(items: list[dict], model: tuple[str, str]) -> list[dict]:
    """One call per item through the harness; raises before or after if the budget is blown."""
    if len(items) * EST_PER_CALL > BUDGET_USD:
        raise RuntimeError(f"budget: {len(items)} items would exceed ${BUDGET_USD}")
    tasks = [(model, it, 0) for it in items]
    with ThreadPoolExecutor(WORKERS) as pool:
        rows = list(pool.map(harness.run_one, tasks))
    spent = sum(r.get("cost_usd") or 0 for r in rows)
    if spent > BUDGET_USD:
        raise RuntimeError(f"budget: run cost ${spent:.4f} exceeds ${BUDGET_USD}")
    return rows


def rank(rows: list[dict], n: int) -> list[dict]:
    scored = [r for r in rows if r.get("fit_score") is not None]
    return sorted(scored, key=lambda r: (-r["fit_score"], r["doi"]))[:n]


def record(seen: dict, d: mailer.Digest, state: tuple[Path, Path]) -> None:
    seen_path, log_path = state
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    seen["dois"] = seen.get("dois", []) + [p["doi"] for p in d.picks]
    seen["last_sent"] = d.run_date.isoformat()
    seen_path.write_text(json.dumps(seen, indent=1))
    with log_path.open("a") as f:
        f.write(f"{d.run_date.isoformat()} sent {len(d.picks)} picks, cost ${d.cost_usd:.4f}\n")


def _args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="render to stdout, send nothing")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--cap", type=int, default=200, help="max preprints pulled per category")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = _args(argv)
    seen, today = load_seen(STATE[0]), date.today()
    if not a.dry_run and not due(seen, today):
        print(f"not due: last digest {seen['last_sent']}, gap < {MIN_GAP_DAYS} days")
        return 0
    items = unseen(fetch_recent(a.days, a.cap), seen)
    rows = score(items, MODEL)
    digest = mailer.Digest(rank(rows, a.top), sum(r.get("cost_usd") or 0 for r in rows), today)
    if a.dry_run:
        print(mailer.text_body(digest))
        return 0
    mailer.send(credentials.load(), digest)
    record(seen, digest, STATE)
    print(f"sent {len(digest.picks)} picks, cost ${digest.cost_usd:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
