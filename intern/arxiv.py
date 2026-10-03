"""arXiv q-bio for the intern.

Verified 2026-10-02 against GET https://export.arxiv.org/api/query: Atom XML, and unlike
bioRxiv it sorts newest-first (sortBy=submittedDate&sortOrder=descending), so paging stops at
the first entry older than the window. <published> is the v1 date, so every row is a first
posting; cross-lists come back with their home category (e.g. cs.LG) as primary_category.
"""

from __future__ import annotations

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

CATS = ("q-bio.GN", "q-bio.QM", "q-bio.BM", "q-bio.PE")
API = "https://export.arxiv.org/api/query?"
PAGE = 200
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode()


def _text(e: ET.Element, tag: str) -> str:
    return " ".join((e.findtext(tag, "", NS)).split())


def parse(xml: str) -> list[dict]:
    rows = []
    for e in ET.fromstring(xml).findall("a:entry", NS):
        aid = _text(e, "a:id").rsplit("/abs/", 1)[-1].rsplit("v", 1)[0]
        rows.append(
            {
                "doi": f"10.48550/arXiv.{aid}",  # resolves to arxiv.org/abs/<id>
                "title": _text(e, "a:title"),
                "abstract": _text(e, "a:summary"),
                "category": e.find("arxiv:primary_category", NS).get("term"),
                "date": _text(e, "a:published")[:10],
                "version": "1",
                "server": "arXiv",
            }
        )
    return rows


def fetch(start: date) -> list[dict]:
    """Every paper in CATS first posted on or after `start`."""
    query = {"search_query": " OR ".join(f"cat:{c}" for c in CATS), "max_results": PAGE}
    query |= {"sortBy": "submittedDate", "sortOrder": "descending"}
    out: list[dict] = []
    while True:
        page = parse(_get(API + urllib.parse.urlencode(query | {"start": len(out)})))
        if not page and not out:  # 14 days of CATS was ~150 papers (2026-10-02), never zero
            raise RuntimeError("arXiv returned an empty feed")
        fresh = [r for r in page if r["date"] >= start.isoformat()]
        out += fresh
        if len(fresh) < PAGE:
            return out
        time.sleep(3)  # arXiv asks for 3 s between calls
