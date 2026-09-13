"""Pins the bootstrap CI math: percentile method, fixed seed, paired difference."""

import math
from pathlib import Path

import pytest

import analyze
import bootstrap

DATA = Path("data/results.jsonl")


def test_ci_is_linear_interpolated_2p5_and_97p5_percentiles():
    # hand computation: position (n-1)*q on the sorted values 1..40 -> 1.975 and 39.025
    assert bootstrap._ci([float(i) for i in range(1, 41)]) == pytest.approx((1.975, 39.025))


def test_constant_errors_give_degenerate_interval():
    lo, hi = bootstrap.mae_ci({"a": 0.3, "b": 0.3, "c": 0.3})
    assert (lo, hi) == (0.3, 0.3)


def test_interval_brackets_the_point_estimate_and_is_reproducible():
    errs = {"a": 0.2, "b": 0.4, "c": 0.0, "d": 0.1}
    lo, hi = bootstrap.mae_ci(errs)
    assert lo <= 0.175 <= hi and lo < hi
    assert bootstrap.mae_ci(errs) == (lo, hi)  # fixed seed
    assert bootstrap._draws(4, 0) != bootstrap._draws(4, 1)


def test_empty_errors_are_nan():
    assert all(math.isnan(v) for v in bootstrap.mae_ci({}))
    assert math.isnan(bootstrap.diff_p({}, {"a": 0.1}))


def test_diff_p_is_one_against_self_and_extreme_when_dominated():
    ref = {"a": 0.1, "b": 0.2, "c": 0.3}
    worse = {k: v + 0.05 for k, v in ref.items()}
    assert bootstrap.diff_p(ref, ref) == 1.0
    assert bootstrap.diff_p(worse, ref) == 0.0
    assert bootstrap.diff_p(ref, worse) == 1.0


def test_diff_p_pairs_on_common_dois_only():
    a = {"x": 0.5, "y": 0.5, "only_a": 9.0}
    b = {"x": 0.5, "y": 0.5, "only_b": 0.0}
    assert bootstrap.diff_p(a, b) == 1.0


@pytest.mark.skipif(not DATA.exists(), reason="published dataset not on disk")
def test_reproduces_prototype_intervals_on_published_data():
    rows = analyze.load_rows(DATA, Path("data/preprints.json"))
    m = analyze.metrics(rows)
    hy3, haiku = m["tencent/hy3"], m["anthropic/claude-haiku-4.5"]
    assert (hy3["mae_lo"], hy3["mae_hi"]) == pytest.approx((0.068, 0.110), abs=0.005)
    assert (haiku["mae_lo"], haiku["mae_hi"]) == pytest.approx((0.117, 0.158), abs=0.005)
    assert hy3["mae_diff_p"] == 1.0  # hy3 is the best usable model, so it is its own reference
