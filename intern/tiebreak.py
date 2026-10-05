"""Secondary keys for papers Hy3 tied at the digest cutoff and DeepSeek did not separate.

In rank order: the corresponding author is at an OpenAlex top-200 institution (by h-index; the
last author stands in when nobody is flagged), the abstract names code or a public dataset, then
TF-IDF similarity to the reader's own past picks: off unless `past_picks` is set in the credentials
file (measured against the author's Journal Safari posts). On the 74 ties of 2026-10-02 none of
the three beat a random order on ceiling fit by a margin one window can show, and none cost any:
the institution key is a stated reader preference (alone it ran slightly against the ceiling,
rho -0.19), the other two are the only free signals that tracked it at all (+0.36, +0.28).

OpenAlex costs $0.0001 a call against a free $0.10/day allowance with no key (response headers,
2026-10-03); a run makes about five calls. A failed fetch skips that key with a warning on
stderr, and the digest still goes out.
"""

from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
from collections import Counter

from intern import credentials

OPENALEX = "https://api.openalex.org/"
DATA = re.compile(
    r"github|gitlab|zenodo|code (is|are) (freely |publicly )?available|open[- ]source|"
    r"uk biobank|all of us|cellxgene|proteingym|clinvar|gnomad|tcga|1000 genomes|\bgeo\b",
    re.I,
)
STOP = frozenset(
    "the and for with that this from are was were which their our its into than then have has "
    "not but can all also these those using use used based between both each more most over "
    "such they them per across within".split()
)
FAILS = (OSError, ValueError, KeyError)  # urllib errors are OSErrors; bad JSON is a ValueError


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode()


def _short(openalex_id: str) -> str:
    return openalex_id.rsplit("/", 1)[-1]


def corresponding_institutions(dois: list[str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for i in range(0, len(dois), 50):  # OpenAlex allows 100 OR values per filter
        page = _get(f"{OPENALEX}works?per_page=50&filter=doi:{'|'.join(dois[i : i + 50])}")
        for w in json.loads(page)["results"]:
            a = w.get("authorships") or []
            a = [x for x in a if x.get("is_corresponding")] or a[-1:]
            ids = {_short(n["id"]) for x in a for n in x.get("institutions", []) if n.get("id")}
            out[w["doi"].removeprefix("https://doi.org/").lower()] = ids
    return out


def past_pick_posts(text: str, prefix: str) -> list[str]:
    """Each post in llms-full.txt opens with '### Title' then 'URL:'; a bare ### is a subhead."""
    starts = list(re.finditer(r"^### (.+)\nURL: ", text, re.M))
    ends = [m.start() for m in starts[1:]] + [len(text)]
    noise = re.compile(r"<[^>]+>|```.*?```|\(http[^)]*\)", re.S)  # tags, frontmatter, link targets
    posts = [noise.sub(" ", text[m.end() : e]) for m, e in zip(starts, ends, strict=True)]
    return [p for m, p in zip(starts, posts, strict=True) if m.group(1).startswith(prefix)]


def _bag(s: str) -> Counter:
    return Counter(w for w in re.findall(r"[a-z][a-z0-9-]{2,}", s.lower()) if w not in STOP)


def similarity(texts: dict[str, str], refs: list[str]) -> dict[str, float]:
    """Max TF-IDF cosine of each text to any ref (sublinear tf, idf over texts + refs)."""
    if not refs:
        raise ValueError("no past-pick posts found at the past_picks url")
    docs, qs = {k: _bag(v) for k, v in texts.items()}, [_bag(r) for r in refs]
    df = Counter(w for c in [*docs.values(), *qs] for w in c)
    n = len(docs) + len(qs)

    def unit(c: Counter) -> dict[str, float]:
        v = {w: (1 + math.log(k)) * math.log(n / df[w]) for w, k in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}

    qv = [unit(q) for q in qs]
    return {
        k: max(sum(x * q.get(w, 0) for w, x in unit(c).items()) for q in qv)
        for k, c in docs.items()
    }


def _institution_key(group: list[dict]) -> None:
    top = {
        _short(i["id"])
        for p in (1, 2)
        for i in json.loads(
            _get(f"{OPENALEX}institutions?per_page=100&page={p}&sort=summary_stats.h_index:desc")
        )["results"]
    }
    corr = corresponding_institutions([r["doi"] for r in group])
    for r in group:
        r["top_inst"] = float(bool(corr.get(r["doi"].lower(), set()) & top))


def _similarity_key(group: list[dict]) -> None:
    picks = credentials.past_picks()
    if picks is None:  # off by default: the reference text is one reader's own history
        return
    url, prefix = picks
    sims = similarity(
        {r["doi"]: f"{r['title']} {r['abstract']}" for r in group},
        past_pick_posts(_get(url), prefix),
    )
    for r in group:
        r["similar"] = sims[r["doi"]]


def annotate(group: list[dict]) -> None:
    """Sets open_data, top_inst and similar on each row; a key whose fetch fails is left unset."""
    for r in group:
        r["open_data"] = float(bool(DATA.search(r.get("abstract") or "")))
    for key in (_institution_key, _similarity_key):
        try:
            key(group)
        except FAILS as e:
            print(f"tiebreak: {key.__name__.strip('_')} skipped ({e})", file=sys.stderr)
