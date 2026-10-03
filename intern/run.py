"""Biweekly run: fetch, dedupe against seen DOIs, score once with the production model, email.

    uv run python -m intern --dry-run     # render the digest to stdout, send nothing
    uv run python -m intern               # what launchd runs every Thursday; sends only if due

The OpenRouter key comes from the environment, or from the credentials file when nothing
exported it (see intern.credentials.ensure_api_key): launchd starts no shell.

launchd has no biweekly primitive, so the plist fires weekly and `due()` refuses to send when
the last digest went out under MIN_GAP_DAYS ago. Budget guard: abort before scoring if the
estimated cost exceeds BUDGET_USD, and again after if the measured cost did.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import fetch_preprints
import harness
from intern import arxiv, credentials, mailer, tiebreak

STATE_DIR = Path("~/.preprint-judge").expanduser()
STATE = (STATE_DIR / "seen.json", STATE_DIR / "intern.log")
MODEL = ("tencent/hy3", "off")  # the gate-approved production judge, reasoning off
# Hy3 scores coarsely: 74 of 948 tied at 0.85 on 2026-10-02. DeepSeek re-scoring that group
# lifted the mean ceiling score of the five picks from 0.69 (random) to 0.84 (Sonnet: 0.88).
RERANK = ("deepseek/deepseek-v4.1-flash", "off")
BUDGET_USD = 0.25  # 14 days on all three servers was 956 first postings (2026-10-02): est $0.10
EST_PER_CALL = 0.0001  # generous: hy3 measured $0.00006
MIN_GAP_DAYS = 13
WORKERS = 8
RETRIES = 2  # the bakeoff calls a model usable when every paper scores within 3 tries


def load_seen(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"dois": [], "last_sent": None}


SERVERS = {"biorxiv": fetch_preprints.IN_LANE, "medrxiv": fetch_preprints.MED_IN_LANE}


def fetch_recent(days: int) -> list[dict]:
    """Every in-lane preprint FIRST posted in the last `days` days, on all three servers.

    The bioRxiv/medRxiv API is oldest-first with no sort option and lists every version posted
    in the window, so page all of it (any cap drops the same days for good, since consecutive
    windows abut) and keep v1 only. The budget guard in score() is what bounds the cost.
    """
    start, end = date.today() - timedelta(days=days), date.today()
    rows = [
        fetch_preprints.slim(r)
        for server, cats in SERVERS.items()
        for c in sorted(cats)
        for r in fetch_preprints.fetch_category(
            c, fetch_preprints.Window(start, end, server), sys.maxsize
        )
        if r["version"] == "1"
    ]
    return [{**r, "lane": "in"} for r in rows + arxiv.fetch(start)]


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
        for _ in range(RETRIES):  # a miss a retry recovers costs a call; a skipped paper is lost
            todo = [i for i, r in enumerate(rows) if r.get("fit_score") is None]
            for i, r in zip(todo, pool.map(harness.run_one, [tasks[i] for i in todo]), strict=True):
                r["cost_usd"] = (r.get("cost_usd") or 0) + (rows[i].get("cost_usd") or 0)
                rows[i] = r
    rows = [
        r | it for r, it in zip(rows, items, strict=True)
    ]  # harness rows cut the title to 120 chars
    spent = sum(r.get("cost_usd") or 0 for r in rows)
    if spent > BUDGET_USD:
        raise RuntimeError(f"budget: run cost ${spent:.4f} exceeds ${BUDGET_USD}")
    return rows


def break_ties(rows: list[dict], n: int) -> float:
    """Re-score with RERANK only the tie group straddling the top-n cutoff; returns its cost."""
    scored = sorted(
        (r for r in rows if r.get("fit_score") is not None), key=lambda r: -r["fit_score"]
    )
    if len(scored) <= n or scored[n - 1]["fit_score"] != scored[n]["fit_score"]:
        return 0.0
    group = [r for r in scored if r["fit_score"] == scored[n - 1]["fit_score"]]
    fields = (
        "doi",
        "title",
        "abstract",
        "category",
        "lane",
    )  # not fit_score: score() keeps item keys
    again = score([{k: r.get(k) for k in fields} for r in group], RERANK)
    for r, a in zip(group, again, strict=True):
        r["tiebreak"] = a.get("fit_score") or 0.0
    tiebreak.annotate(group)  # institution, open data, similarity: free, for what DeepSeek ties
    return sum(a.get("cost_usd") or 0 for a in again)


def rank(rows: list[dict], n: int) -> list[dict]:
    scored = [r for r in rows if r.get("fit_score") is not None]
    # ponytail: ties broken by DOI hash, neutral across servers (a raw DOI sort gave every 0.85
    # tie to arXiv's prefix). Still a lottery among ties (171 of 1,790 scored exactly 0.85 in a
    # 60-day pull, 2026-09-29): rerank ties with a second judge if that matters.
    return sorted(
        scored,
        key=lambda r: (
            -r["fit_score"],
            -r.get("tiebreak", 0.0),
            *(-r.get(k, 0.0) for k in ("top_inst", "open_data", "similar")),
            hashlib.sha256(r["doi"].encode()).hexdigest(),
        ),
    )[:n]


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
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    a = _args(argv)
    credentials.ensure_api_key()
    seen, today = load_seen(STATE[0]), date.today()
    if not a.dry_run and not due(seen, today):
        print(f"not due: last digest {seen['last_sent']}, gap < {MIN_GAP_DAYS} days")
        return 0
    items = unseen(fetch_recent(a.days), seen)
    rows = score(items, MODEL)
    cost = sum(r.get("cost_usd") or 0 for r in rows) + break_ties(rows, a.top)
    digest = mailer.Digest(rank(rows, a.top), cost, today)
    if a.dry_run:
        print(mailer.text_body(digest))
        return 0
    mailer.send(credentials.load(), digest)
    record(seen, digest, STATE)
    print(f"sent {len(digest.picks)} picks, cost ${digest.cost_usd:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
