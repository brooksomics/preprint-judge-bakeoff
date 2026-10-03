"""Pins the secondary tie-break keys: institution, open data, similarity to past picks."""

import json
import urllib.error

from intern import tiebreak

POSTS = """# B. Brooks

## Blog posts

### Not a safari
URL: https://example.org/blog/a/

single cell atlas annotation

---

### Journal Safari: Protein models
URL: https://example.org/blog/b/

```yaml
tags: [frontmatter-word]
```
protein language model variant effect prediction
### A subheading inside the post
more protein variant text

---
"""


def fake_get(responses: dict):
    def get(url):
        return next(body for key, body in responses.items() if key in url)

    return get


def test_journal_safari_posts_keeps_only_safari_sections_whole():
    [post] = tiebreak.journal_safari_posts(POSTS)
    assert "protein language model" in post and "more protein variant text" in post
    assert "single cell" not in post and "frontmatter-word" not in post


def test_annotate_sets_all_three_keys(monkeypatch):
    inst = lambda i: {"institutions": [{"id": f"https://openalex.org/{i}"}]}  # noqa: E731
    works = {
        "results": [
            {
                "doi": "https://doi.org/10.1/a",
                "authorships": [
                    {"is_corresponding": False, **inst("I9")},
                    {"is_corresponding": True, **inst("I1")},
                ],
            },
            {  # nobody flagged: the last author stands in, and I9 is not top-tier
                "doi": "https://doi.org/10.1/b",
                "authorships": [{**inst("I1")}, {**inst("I9")}],
            },
        ]
    }
    top = {"results": [{"id": "https://openalex.org/I1"}]}
    monkeypatch.setattr(
        tiebreak,
        "_get",
        fake_get({"institutions?": json.dumps(top), "works?": json.dumps(works), "llms": POSTS}),
    )
    group = [
        {"doi": "10.1/A", "title": "Protein language model", "abstract": "variant effect; GitHub"},
        {"doi": "10.1/b", "title": "Soil survey", "abstract": "field ecology"},
    ]
    tiebreak.annotate(group)
    a, b = group
    assert (a["top_inst"], b["top_inst"]) == (1.0, 0.0)
    assert (a["open_data"], b["open_data"]) == (1.0, 0.0)
    assert a["similar"] > b["similar"]


def test_annotate_survives_openalex_and_site_outages(monkeypatch, capsys):
    def down(url):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(tiebreak, "_get", down)
    group = [{"doi": "10.1/a", "title": "t", "abstract": "data deposited on Zenodo"}]
    tiebreak.annotate(group)
    assert group[0]["open_data"] == 1.0 and "top_inst" not in group[0]
    assert "similar" not in group[0] and "skipped" in capsys.readouterr().err
