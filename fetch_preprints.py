"""Pull recent bioRxiv preprints and pick a stratified in-lane / off-lane set.

Verified 2026-09-11 against
GET https://api.biorxiv.org/details/biorxiv/{from}/{to}/{cursor}?category={snake_case}
which returns {"messages": [{"status": "ok", "category": "plant biology", "total": "67", ...}],
"collection": [{title, abstract, doi, date, version, category, ...}]}, 30 rows per page, with
`cursor` as the row offset. Category names come back lowercase with spaces.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import date, timedelta
from itertools import chain, zip_longest
from pathlib import Path

API = "https://api.biorxiv.org/details/biorxiv/{start}/{end}/{cursor}?category={cat}"
IN_LANE = {"bioinformatics", "genomics", "systems biology", "microbiology"}
OFF_LANE = {
    "neuroscience",
    "plant biology",
    "biophysics",
    "ecology",
    "paleontology",
    "zoology",
    "animal behavior and cognition",
}
FIELDS = ("doi", "title", "abstract", "category", "date", "version")
PAGE = 30


def _get(url: str, attempt: int = 1) -> dict:
    """bioRxiv's API stalls mid-pagination now and then; retry a page up to 3 times."""
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            page = json.load(r)
    except (TimeoutError, OSError):
        if attempt >= 3:
            raise
        time.sleep(3)
        return _get(url, attempt + 1)
    if page["messages"][0].get("status") != "ok":
        raise RuntimeError(f"bioRxiv: {page['messages'][0]}")
    return page


def fetch_category(cat: str, window: tuple[date, date], cap: int) -> list[dict]:
    """Pages one category until `total` or `cap` rows."""
    rows: list[dict] = []
    while True:
        url = API.format(
            start=window[0], end=window[1], cursor=len(rows), cat=cat.replace(" ", "_")
        )
        page = _get(url)
        batch = page.get("collection", [])
        rows += batch
        if len(batch) < PAGE or len(rows) >= min(cap, int(page["messages"][0]["total"])):
            return rows[:cap]


def stratify(items: list[dict], categories: set[str], n: int) -> list[dict]:
    """Round-robin across categories, DOI-deduped, deterministic (sorted by DOI)."""
    lane = "in" if categories <= IN_LANE else "off"
    seen: set[str] = set()
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for it in sorted(items, key=lambda i: (i["doi"], i["version"])):
        if it["category"] in categories and it["doi"] not in seen:
            seen.add(it["doi"])
            by_cat[it["category"]].append(it)
    rr = chain.from_iterable(zip_longest(*(by_cat[c] for c in sorted(by_cat))))
    return [{**it, "lane": lane} for it in rr if it is not None][:n]


def main() -> None:  # pragma: no cover
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=21)
    ap.add_argument("--in-lane", type=int, default=60)
    ap.add_argument("--off-lane", type=int, default=30)
    ap.add_argument("--cap", type=int, default=120, help="max rows pulled per category")
    ap.add_argument("--out", type=Path, default=Path("data/preprints.json"))
    a = ap.parse_args()
    window = (date.today() - timedelta(days=a.days), date.today())
    rows = [r for c in sorted(IN_LANE | OFF_LANE) for r in fetch_category(c, window, a.cap)]
    slim = [{k: r.get(k) for k in FIELDS} for r in rows]
    picked = stratify(slim, IN_LANE, a.in_lane) + stratify(slim, OFF_LANE, a.off_lane)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(picked, indent=1))
    print(f"{len(rows)} rows fetched over {window[0]}..{window[1]}; kept {len(picked)}")
    for lane in ("in", "off"):
        cats = Counter(p["category"] for p in picked if p["lane"] == lane)
        print(f"  {lane}-lane {sum(cats.values())}: {dict(cats)}")


if __name__ == "__main__":
    main()
