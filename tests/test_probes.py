"""Pins the length probe: word counts attached to rows, Spearman(len, score), flag vs ceiling."""

import json
import math

import pytest

import analyze
import probes


def _by_item(pairs):
    return {str(i): [{"fit_score": s, "n_words": n}] for i, (s, n) in enumerate(pairs)}


def test_len_rho_is_spearman_of_item_mean_vs_abstract_length():
    assert probes.len_rho(_by_item([(0.1, 100), (0.5, 200), (0.9, 300)])) == pytest.approx(1.0)
    assert probes.len_rho(_by_item([(0.9, 100), (0.5, 200), (0.1, 300)])) == pytest.approx(-1.0)


def test_len_rho_skips_unscored_and_unmeasured_items():
    by = _by_item([(0.1, 100), (0.5, 200), (0.9, 300), (None, 400)])
    by["5"] = [{"fit_score": 0.0}]  # no n_words -> ignored
    assert probes.len_rho(by) == pytest.approx(1.0)
    assert math.isnan(probes.len_rho(_by_item([(0.1, 100), (0.5, 200)])))


def test_flagged_lists_models_whose_rho_departs_from_the_ceiling():
    m = {
        "c": {"len_rho": 0.10},
        "far": {"len_rho": 0.35},
        "near": {"len_rho": -0.05},
        "nan": {"len_rho": math.nan},
    }
    assert probes.flagged(m, "c") == ["far"]


def test_load_rows_attaches_abstract_word_count(tmp_path):
    (tmp_path / "p.json").write_text(json.dumps([{"doi": "x", "lane": "off", "abstract": "a b c"}]))
    r = {"label": "m", "doi": "x", "run_idx": 0, "fit_score": 0.9}
    (tmp_path / "r.jsonl").write_text(json.dumps(r) + "\n")
    got = analyze.load_rows(tmp_path / "r.jsonl", tmp_path / "p.json")
    assert got == [{**r, "lane": "off", "n_words": 3, "parse_tier": None}]
