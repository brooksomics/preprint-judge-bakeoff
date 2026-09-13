"""Pins the disagreement audit: usable-model filter, per-item spread, extremes, mirror list."""

import pytest

import disagreement

CEILING = "ceil"
SPEC = disagreement.Spec(ceiling=CEILING, n=2)


def _rows():
    scores = {  # label -> doi -> score (one run each is enough for the audit)
        CEILING: {"a": 0.6, "b": 0.5, "c": 0.5},
        "hi": {"a": 0.9, "b": 0.5, "c": 0.5},
        "lo": {"a": 0.1, "b": 0.5, "c": 0.5},
        "mid": {"a": 0.5, "b": 0.6, "c": 0.5},
        "flaky": {"a": 0.0, "b": 0.0, "c": 0.0},  # below the coverage floor, must be ignored
    }
    meta = {
        "a": ("A title", "genomics", "in"),
        "b": ("B title", "ecology", "off"),
        "c": ("C", "x", "in"),
    }
    return [
        {
            "label": lab,
            "doi": d,
            "run_idx": 0,
            "fit_score": s,
            "title": meta[d][0],
            "category": meta[d][1],
            "lane": meta[d][2],
        }
        for lab, ds in scores.items()
        for d, s in ds.items()
    ]


def _metrics():
    return {k: {"cov": 100.0} for k in (CEILING, "hi", "lo", "mid")} | {"flaky": {"cov": 50.0}}


def test_usable_labels_excludes_ceiling_and_low_coverage():
    assert disagreement.usable_labels(_metrics(), CEILING) == ["hi", "lo", "mid"]


def test_rank_orders_by_population_stdev_and_names_the_extremes():
    top, bottom = disagreement.rank(_rows(), _metrics(), SPEC)
    assert [r["doi"] for r in top] == ["a", "b"]
    a = top[0]
    assert a["sd"] == pytest.approx(0.3266, abs=1e-3)  # pstdev(0.9, 0.1, 0.5)
    assert (a["lo"], a["lo_model"], a["hi"], a["hi_model"]) == (0.1, "lo", 0.9, "hi")
    assert a["ceiling"] == 0.6 and a["title"] == "A title" and a["lane"] == "in"
    assert [r["doi"] for r in bottom] == ["c", "b"]  # mirror: lowest spread first


def test_markdown_has_both_tables_and_the_model_count():
    md = disagreement.markdown(_rows(), _metrics(), SPEC)
    assert "3 usable models" in md
    assert md.count("| sd |") == 2 and "A title" in md and "10.1101" not in md
