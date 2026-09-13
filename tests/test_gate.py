"""Pins gate.py: PASS/FAIL per check, exit 0/1, and the live model-id check (mocked)."""

import csv
from pathlib import Path

import pytest

import gate

ROW = {"label": "x/m", "cov": "99.5", "mae_hi": "0.11", "top10": "6", "violations": "1"}
ARGS = [
    "--model",
    "x/m",
    "--min-cov",
    "99",
    "--max-mae-hi",
    "0.12",
    "--min-top10",
    "5",
    "--max-violations",
    "2",
]


@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "results.csv"
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ROW))
        w.writeheader()
        w.writerow(ROW)
    return p


def test_checks_pass_and_fail_on_thresholds():
    ok = gate.checks(ROW, gate.Thresholds(99, 0.12, 5, 2))
    assert all(passed for _, passed, _ in ok) and len(ok) == 4
    bad = dict(gate.checks(ROW, gate.Thresholds(99.9, 0.10, 7, 0)))  # every threshold missed
    assert not any(passed for passed, _ in bad.values())


def test_main_passes_and_exits_zero(csv_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "live_model_ids", lambda: {"x/m", "y/n"})
    assert gate.main([*ARGS, "--csv", str(csv_path)]) == 0
    out = capsys.readouterr().out
    assert out.count("PASS") == 5 and "FAIL" not in out and out.strip().endswith("PASS")


def test_main_fails_on_a_threshold(csv_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "live_model_ids", lambda: {"x/m"})
    assert gate.main([*ARGS, "--csv", str(csv_path), "--max-mae-hi", "0.10"]) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "mae_hi" in out and out.strip().endswith("FAIL")


def test_main_fails_when_model_id_is_gone(csv_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "live_model_ids", lambda: {"someone/else"})
    assert gate.main([*ARGS, "--csv", str(csv_path)]) == 1
    assert "not listed" in capsys.readouterr().out


def test_main_fails_when_model_row_is_missing(csv_path, monkeypatch):
    monkeypatch.setattr(gate, "live_model_ids", lambda: {"x/m"})
    assert gate.main(["--model", "nope/z", "--csv", str(csv_path)]) == 1


def test_live_model_ids_reads_the_openrouter_shape(monkeypatch):
    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"data": [{"id": "a/b"}, {"id": "c/d"}], "total_count": 2}'

    monkeypatch.setattr(gate.urllib.request, "urlopen", lambda url, timeout: Resp())
    assert gate.live_model_ids() == {"a/b", "c/d"}
    assert Path(gate.MODELS_URL).name == "models"
