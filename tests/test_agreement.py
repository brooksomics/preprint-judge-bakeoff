"""Pins chance-corrected agreement: kappa on a hand-worked 2x2, alpha over 0.1 bins, verdicts."""

import math

import pytest

import agreement

CEILING = "ceil"


def test_cohen_kappa_on_a_hand_worked_2x2():
    # 10 yes/yes, 5 no/no, 3 yes/no, 2 no/yes -> po = .75, pe = .65*.6 + .35*.4 = .53
    pairs = [(1, 1)] * 10 + [(0, 0)] * 5 + [(1, 0)] * 3 + [(0, 1)] * 2
    assert agreement.cohen_kappa(pairs) == pytest.approx((0.75 - 0.53) / (1 - 0.53))
    assert agreement.cohen_kappa([(1, 1), (1, 1)]) == 1.0  # both constant and identical
    assert math.isnan(agreement.cohen_kappa([]))


def test_alpha_ordinal_hand_worked():
    assert agreement.alpha_ordinal([(0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]) == 1.0
    # bins (0,1),(1,0): D_o = 4, D_e = 8/3 -> alpha = -0.5
    assert agreement.alpha_ordinal([(0.0, 0.1), (0.1, 0.0)]) == pytest.approx(-0.5)
    assert agreement.alpha_ordinal([(0.5, 0.5)]) == 1.0
    assert math.isnan(agreement.alpha_ordinal([]))


def test_kappa_band_follows_landis_koch():
    assert [agreement.kappa_band(k) for k in (-0.1, 0.1, 0.3, 0.5, 0.7, 0.9)] == [
        "worse than chance",
        "slight",
        "fair",
        "moderate",
        "substantial",
        "almost perfect",
    ]


def test_kappa_shortlist_and_top_n_use_the_decision_not_the_score():
    means = {"a": 0.9, "b": 0.6, "c": 0.4, "d": 0.1}
    ceiling = {"a": 0.7, "b": 0.45, "c": 0.55, "d": 0.2}  # b and c flip across 0.5
    pairs = agreement.decision_pairs(means, ceiling)
    assert pairs == [(1, 1), (1, 0), (0, 1), (0, 0)]
    assert agreement.cohen_kappa(pairs) == pytest.approx(0.0)
    assert agreement.kappa_top({"a", "b"}, {"a", "c"}, list("abcd")) == pytest.approx(0.0)
    assert agreement.kappa_top({"a", "b"}, {"a", "b"}, list("abcd")) == 1.0


def _rows():
    cats = {
        "a": ("genomics", "in"),
        "b": ("genomics", "in"),
        "c": ("ecology", "off"),
        "d": ("zoology", "off"),
    }
    out = []
    for lab, scores in {CEILING: (0.9, 0.2, 0.1, 0.8), "m": (0.8, 0.3, 0.1, 0.9)}.items():
        for doi, s in zip("abcd", scores, strict=True):
            out.append(
                {
                    "label": lab,
                    "doi": doi,
                    "run_idx": 0,
                    "fit_score": s,
                    "category": cats[doi][0],
                    "lane": cats[doi][1],
                }
            )
    return out


def test_per_category_pools_off_lane_and_applies_the_verdict_rule():
    table = agreement.per_category(_rows(), CEILING)
    by = {(r["label"], r["category"]): r for r in table}
    assert set(by) == {("m", "genomics"), ("m", "off-lane"), ("m", "all")}
    g = by[("m", "genomics")]
    assert g["n"] == 2 and g["kappa_0.5"] == 1.0 and g["verdict"] == "not reliable (n < 8)"
    assert by[("m", "all")]["n"] == 4


def test_verdict_rule():
    assert agreement.verdict(0.6, 8) == "reliable"
    assert agreement.verdict(0.59, 8) == "not reliable"
    assert agreement.verdict(0.9, 7) == "not reliable (n < 8)"
    assert agreement.verdict(math.nan, 8) == "not reliable"
