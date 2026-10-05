"""Pins the intern's arXiv fetch: Atom parsing, and paging that stops at the window edge."""

from datetime import date

import pytest

from intern import arxiv


def entry(aid: str, published: str, primary: str = "q-bio.GN") -> str:
    return f"""<entry>
    <id>http://arxiv.org/abs/{aid}</id>
    <title>A  title
      on two lines</title>
    <summary>An abstract.
    </summary>
    <published>{published}T15:41:24Z</published>
    <arxiv:primary_category term="{primary}"/>
  </entry>"""


def feed(*entries: str) -> str:
    return (
        '<feed xmlns:arxiv="http://arxiv.org/schemas/atom" xmlns="http://www.w3.org/2005/Atom">'
        + "".join(entries)
        + "</feed>"
    )


def test_parse_strips_the_version_and_whitespace():
    [row] = arxiv.parse(feed(entry("2610.01891v2", "2026-10-01", "cs.CE")))
    assert row == {
        "doi": "10.48550/arXiv.2610.01891",
        "title": "A title on two lines",
        "abstract": "An abstract.",
        "category": "cs.CE",
        "date": "2026-10-01",
        "version": "1",
        "server": "arXiv",
    }


def test_fetch_pages_newest_first_until_the_window_edge(monkeypatch):
    pages = [
        feed(entry("3v1", "2026-10-01"), entry("2v1", "2026-09-30")),
        feed(entry("1v1", "2026-09-20"), entry("0v1", "2026-09-10")),
        feed(entry("never", "2026-09-01")),
    ]
    urls = []
    monkeypatch.setattr(arxiv, "PAGE", 2)
    monkeypatch.setattr(arxiv.time, "sleep", lambda s: None)
    monkeypatch.setattr(arxiv, "_get", lambda url: urls.append(url) or pages[len(urls) - 1])
    rows = arxiv.fetch(date(2026, 9, 18))
    assert [r["doi"][-1] for r in rows] == ["3", "2", "1"]
    assert len(urls) == 2 and "sortOrder=descending" in urls[0] and "start=2" in urls[1]


def test_fetch_refuses_an_empty_feed(monkeypatch):
    monkeypatch.setattr(arxiv, "_get", lambda url: feed())
    with pytest.raises(RuntimeError, match="arXiv"):
        arxiv.fetch(date(2026, 9, 18))
