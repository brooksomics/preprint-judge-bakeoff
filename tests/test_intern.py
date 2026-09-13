"""Pins the production intern: credentials, digest rendering, dedupe, cadence, budget, SMTP."""

import json
from datetime import date

import pytest

from intern import credentials, mailer, run

PICKS = [
    {
        "doi": "10.1101/2026.09.01.1",
        "version": "2",
        "title": "Alpha paper",
        "fit_score": 0.91,
        "field": "genomics",
        "rationale": "Directly on a listed interest.",
        "cost_usd": 0.00005,
    },
    {
        "doi": "10.1101/2026.09.02.2",
        "version": "1",
        "title": "Beta paper",
        "fit_score": 0.72,
        "field": "microbiome",
        "rationale": "Routine but in lane.",
        "cost_usd": 0.00007,
    },
]
DIGEST = mailer.Digest(picks=PICKS, cost_usd=0.0312, run_date=date(2026, 9, 17))
CREDS = credentials.Gmail(sender="me@example.com", app_password="pw", receiver="me@example.com")


def test_credentials_missing_file_and_bad_shape(tmp_path):
    with pytest.raises(FileNotFoundError):
        credentials.load(tmp_path / "nope.json")
    (tmp_path / "bad.json").write_text(json.dumps({"gmail": {"sender": "x"}}))
    with pytest.raises(ValueError, match="app_password"):
        credentials.load(tmp_path / "bad.json")


def test_credentials_shape(tmp_path):
    p = tmp_path / "credentials.json"
    p.write_text(
        json.dumps(
            {
                "gmail": {"sender": "a@example.com", "app_password": "p q"},
                "receiver": "b@example.com",
            }
        )
    )
    assert credentials.load(p) == credentials.Gmail("a@example.com", "p q", "b@example.com")


def test_subject_and_bodies():
    assert mailer.subject(DIGEST) == "Preprint intern: 2 picks for 2026-09-17"
    html, text = mailer.html_body(DIGEST), mailer.text_body(DIGEST)
    assert 'href="https://www.biorxiv.org/content/10.1101/2026.09.01.1v2"' in html
    assert "0.91" in html and "genomics" in html and "Directly on a listed interest." in html
    assert "$0.0312" in html and "$0.0312" in text and "Beta paper" in text
    msg = mailer.build(CREDS, DIGEST)
    assert msg["To"] == "me@example.com" and msg.get_content_type() == "multipart/alternative"


def test_send_uses_smtp_ssl_on_465(monkeypatch):
    calls = {}

    class FakeSMTP:
        def __init__(self, host, port):
            calls["conn"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, pw):
            calls["login"] = (user, pw)

        def sendmail(self, frm, to, body):
            calls["sent"] = (frm, to, "Alpha paper" in body)

    monkeypatch.setattr(mailer.smtplib, "SMTP_SSL", FakeSMTP)
    mailer.send(CREDS, DIGEST)
    assert calls["conn"] == ("smtp.gmail.com", 465)
    assert calls["login"] == ("me@example.com", "pw")
    assert calls["sent"] == ("me@example.com", "me@example.com", True)


def test_unseen_drops_delivered_dois():
    seen = {"dois": ["10.1101/2026.09.01.1"], "last_sent": None}
    items = [{"doi": p["doi"]} for p in PICKS]
    assert run.unseen(items, seen) == [{"doi": "10.1101/2026.09.02.2"}]


def test_due_enforces_the_biweekly_gap():
    today = date(2026, 9, 17)
    assert run.due({"last_sent": None}, today)
    assert run.due({"last_sent": "2026-09-04"}, today)  # 13 days
    assert not run.due({"last_sent": "2026-09-05"}, today)  # 12 days


def test_budget_guard_before_and_after_scoring(monkeypatch):
    items = [{"doi": str(i)} for i in range(2000)]
    with pytest.raises(RuntimeError, match="budget"):
        run.score(items, ("m", "off"))
    monkeypatch.setattr(run.harness, "run_one", lambda t: {"doi": t[1]["doi"], "cost_usd": 0.06})
    with pytest.raises(RuntimeError, match="budget"):
        run.score(items[:2], ("m", "off"))


def test_rank_takes_scored_items_only():
    rows = [
        {"doi": "a", "fit_score": 0.2},
        {"doi": "b", "fit_score": None},
        {"doi": "c", "fit_score": 0.9},
    ]
    assert [r["doi"] for r in run.rank(rows, 5)] == ["c", "a"]


def test_record_appends_dois_and_log(tmp_path):
    seen_path, log_path = tmp_path / "seen.json", tmp_path / "intern.log"
    seen = {"dois": ["old"], "last_sent": None}
    run.record(seen, DIGEST, (seen_path, log_path))
    saved = json.loads(seen_path.read_text())
    assert (
        saved["dois"] == ["old", PICKS[0]["doi"], PICKS[1]["doi"]]
        and saved["last_sent"] == "2026-09-17"
    )
    assert "2 picks" in log_path.read_text() and "$0.0312" in log_path.read_text()


def test_dry_run_renders_and_sends_nothing(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(run, "STATE", (tmp_path / "seen.json", tmp_path / "intern.log"))
    monkeypatch.setattr(
        run, "fetch_recent", lambda days, cap: [{**p, "abstract": "x"} for p in PICKS]
    )
    monkeypatch.setattr(run.harness, "run_one", lambda t: {**t[1], "cost_usd": 0.00005})
    monkeypatch.setattr(mailer, "send", lambda *a: pytest.fail("must not send"))
    assert run.main(["--dry-run", "--top", "1"]) == 0
    out = capsys.readouterr().out
    assert (
        "Preprint intern: 1 picks for" in out and "Alpha paper" in out and "Beta paper" not in out
    )
    assert not (tmp_path / "seen.json").exists()


def test_live_run_sends_and_records(monkeypatch, tmp_path):
    seen_path = tmp_path / "seen.json"
    monkeypatch.setattr(run, "STATE", (seen_path, tmp_path / "intern.log"))
    monkeypatch.setattr(
        run, "fetch_recent", lambda days, cap: [{**p, "abstract": "x"} for p in PICKS]
    )
    monkeypatch.setattr(run.harness, "run_one", lambda t: {**t[1], "cost_usd": 0.00005})
    monkeypatch.setattr(credentials, "load", lambda: CREDS)
    sent = []
    monkeypatch.setattr(mailer, "send", lambda creds, digest: sent.append(digest))
    assert run.main([]) == 0
    assert len(sent) == 1 and len(sent[0].picks) == 2
    assert json.loads(seen_path.read_text())["last_sent"] == date.today().isoformat()
    assert run.main([]) == 0 and len(sent) == 1  # not due again: nothing sent
