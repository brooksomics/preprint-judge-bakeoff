"""Pins the zero-LLM control: tokenizer, tf-idf, cosine, min-max, synthetic rows, Spearman."""

import json
import math

import pytest

import baseline
import rankstats


def test_tokenize_lowercases_keeps_hyphens_digits_and_drops_short_tokens():
    assert baseline.tokenize("Single-cell RNA-seq of 10x data, an ML atlas") == [
        "single-cell",
        "rna-seq",
        "data",
        "atlas",
    ]


def test_idf_is_smoothed_log_ratio():
    docs = [["a", "b"], ["a", "c"], ["a"]]
    w = baseline.idf(docs)
    assert w["a"] == pytest.approx(math.log(4 / 4))  # in every doc -> 0 weight
    assert w["b"] == pytest.approx(math.log(4 / 2))


def test_vector_uses_sublinear_tf_times_idf_and_ignores_unknown_terms():
    w = {"a": 1.0, "b": 2.0}
    assert baseline.vector(["a", "a", "b", "zzz"], w) == {"a": 1 + math.log(2), "b": 2.0}


def test_cosine_bounds():
    assert baseline.cosine({"a": 1.0, "b": 1.0}, {"a": 2.0, "b": 2.0}) == pytest.approx(1.0)
    assert baseline.cosine({"a": 1.0}, {"b": 1.0}) == 0.0
    assert baseline.cosine({}, {"b": 1.0}) == 0.0


def test_minmax_maps_to_unit_interval_and_handles_constant():
    assert baseline.minmax({"x": 2.0, "y": 4.0, "z": 3.0}) == {"x": 0.0, "y": 1.0, "z": 0.5}
    assert baseline.minmax({"x": 1.0, "y": 1.0}) == {"x": 0.0, "y": 0.0}


def test_rows_are_one_synthetic_call_per_preprint(tmp_path):
    pre = [
        {"doi": "1", "title": "metagenomic assembly", "abstract": "contamination", "lane": "in"},
        {"doi": "2", "title": "bird song", "abstract": "zebra finch neurons", "lane": "off"},
    ]
    (tmp_path / "p.json").write_text(json.dumps(pre))
    (tmp_path / "profile.md").write_text("I read metagenomic assembly and contamination papers.")
    rows = baseline.rows(tmp_path / "p.json", tmp_path / "profile.md")
    assert [r["doi"] for r in rows] == ["1", "2"]
    assert rows[0]["label"] == "baseline:tfidf" and rows[0]["lane"] == "in"
    assert rows[0]["fit_score"] == 1.0 and rows[1]["fit_score"] == 0.0
    assert rows[0]["cost_usd"] == 0.0 and rows[0]["run_idx"] == 0 and rows[0]["strict_json"]


def test_ranks_average_ties():
    assert rankstats.ranks([10, 30, 20, 30]) == [1.0, 3.5, 2.0, 3.5]


def test_spearman_extremes_and_degenerate_cases():
    assert rankstats.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert rankstats.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert rankstats.spearman([1, 2, 3, 4], [1, 3, 2, 4]) == pytest.approx(0.8)
    assert math.isnan(rankstats.spearman([1, 2], [1, 2]))
    assert math.isnan(rankstats.spearman([1, 1, 1], [1, 2, 3]))
