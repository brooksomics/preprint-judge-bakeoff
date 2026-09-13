"""Pins the ensemble rows: median of component means, summed cost, max latency, all-or-nothing."""

import pytest

import analyze
import ensembles
import report

CEILING = "ceil"
COMBO = ("lab/a", "lab/b", "lab/c@low")


def _row(label, doi, run, score, cost, lat):
    return {
        "label": label,
        "doi": doi,
        "run_idx": run,
        "fit_score": score,
        "cost_usd": cost,
        "latency_s": lat,
        "lane": "in",
        "title": f"T{doi}",
        "category": "genomics",
    }


def _rows():
    return [
        _row(CEILING, "x", 0, 0.5, 0.01, 1.0),
        _row(CEILING, "y", 0, 0.9, 0.01, 1.0),
        # item x: component means 0.2, 0.6, 0.9 -> median 0.6; costs 1e-4 + 2e-4 + 3e-4
        _row("lab/a", "x", 0, 0.1, 1e-4, 1.0),
        _row("lab/a", "x", 1, 0.3, 1e-4, 3.0),
        _row("lab/b", "x", 0, 0.6, 2e-4, 2.0),
        _row("lab/c@low", "x", 0, 0.9, 3e-4, 5.0),
        # item y: lab/b never scored -> the ensemble has no score either
        _row("lab/a", "y", 0, 0.8, 1e-4, 1.0),
        _row("lab/b", "y", 0, None, 2e-4, 9.0),
        _row("lab/c@low", "y", 0, 0.7, 3e-4, 1.0),
    ]


def test_label_uses_short_names():
    assert ensembles.label(COMBO) == "ens:a+b+c@low"


def test_rows_take_median_sum_cost_and_max_latency():
    out = {r["doi"]: r for r in ensembles.rows(_rows(), COMBO)}
    x, y = out["x"], out["y"]
    assert x["label"] == "ens:a+b+c@low" and x["lane"] == "in" and x["title"] == "Tx"
    assert x["fit_score"] == pytest.approx(0.6)
    assert x["cost_usd"] == pytest.approx(6e-4)
    assert x["latency_s"] == 5.0  # max over components of their per-item mean (lab/a = 2.0)
    assert y["fit_score"] is None and y["cost_usd"] == pytest.approx(6e-4)


def test_all_rows_skips_combos_with_missing_components(monkeypatch):
    monkeypatch.setattr(ensembles, "ENSEMBLES", [COMBO, ("lab/a", "nope/z", "lab/b")])
    out = ensembles.all_rows(_rows())
    assert {r["label"] for r in out} == {"ens:a+b+c@low"} and len(out) == 2


def test_metrics_flag_derived_and_never_pick_it_as_reference(tmp_path, monkeypatch):
    monkeypatch.setattr(ensembles, "ENSEMBLES", [COMBO])
    rows = _rows()
    rows += ensembles.all_rows(rows)
    m = analyze.metrics(rows, CEILING)
    e = m["ens:a+b+c@low"]
    assert e["derived"] is True and m["lab/a"]["derived"] is False
    assert e["cov"] == 50.0 and e["mae"] == pytest.approx(0.1)  # |0.6 - 0.5| on the one item
    assert analyze.best_usable(m, CEILING) != "ens:a+b+c@low"
    report.write_tables(m, tmp_path)
    assert ",derived" in (tmp_path / "results.csv").read_text().splitlines()[0]
    md = (tmp_path / "results.md").read_text()
    assert "| _ens:a+b+c@low_ |" in md and "| lab/a |" in md
