"""Pins the production intern: credentials, digest rendering, dedupe, cadence, budget, SMTP."""

import json
import os
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


def test_ensure_api_key_prefers_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "from-env")
    p = tmp_path / "credentials.json"
    p.write_text(json.dumps({"openrouter_api_key": "from-file"}))
    credentials.ensure_api_key(p)
    assert os.environ["OPENROUTER_API_KEY"] == "from-env"


def test_ensure_api_key_falls_back_to_the_credentials_file(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    p = tmp_path / "credentials.json"
    p.write_text(json.dumps({"gmail": {}, "openrouter_api_key": "from-file"}))
    credentials.ensure_api_key(p)
    assert os.environ["OPENROUTER_API_KEY"] == "from-file"


@pytest.mark.parametrize("body", [{}, {"openrouter_api_key": "   "}])
def test_ensure_api_key_raises_when_there_is_none(tmp_path, monkeypatch, body):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    p = tmp_path / "credentials.json"
    p.write_text(json.dumps(body))
    with pytest.raises(RuntimeError, match="openrouter_api_key"):
        credentials.ensure_api_key(p)
    with pytest.raises(RuntimeError, match="openrouter_api_key"):
        credentials.ensure_api_key(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "body, expected",
    [
        ({}, None),
        ({"past_picks": None}, None),
        ({"past_picks": {"url": " ", "title_prefix": "X"}}, None),
        ({"past_picks": {"url": "https://a/llms.txt"}}, ("https://a/llms.txt", "")),
        (
            {"past_picks": {"url": "https://a/l", "title_prefix": "Safari"}},
            ("https://a/l", "Safari"),
        ),
    ],
)
def test_past_picks_is_off_by_default(tmp_path, body, expected):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(body))
    assert credentials.past_picks(path) == expected
    assert credentials.past_picks(tmp_path / "missing.json") is None


def test_subject_and_bodies():
    assert mailer.subject(DIGEST) == "Preprint intern: 2 picks for 2026-09-17"
    html, text = mailer.html_body(DIGEST), mailer.text_body(DIGEST)
    assert 'href="https://doi.org/10.1101/2026.09.01.1"' in html
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
    items = [{"doi": str(i)} for i in range(int(run.BUDGET_USD / run.EST_PER_CALL) + 1)]
    with pytest.raises(RuntimeError, match="budget"):
        run.score(items, ("m", "off"))
    monkeypatch.setattr(
        run.harness, "run_one", lambda t: {"doi": t[1]["doi"], "cost_usd": run.BUDGET_USD}
    )
    with pytest.raises(RuntimeError, match="budget"):
        run.score(items[:2], ("m", "off"))


def test_fetch_recent_pages_the_whole_window_v1_only_on_all_servers(monkeypatch):
    def fake_category(cat, window, cap):  # oldest-first, like the real API
        n = 250 if cat == "bioinformatics" else 1
        rows = [{"doi": f"{cat}/{i}", "version": "1", "server": window.server} for i in range(n)]
        return (rows + [{"doi": f"{cat}/revised", "version": "2", "server": window.server}])[:cap]

    monkeypatch.setattr(run.fetch_preprints, "fetch_category", fake_category)
    monkeypatch.setattr(run.arxiv, "fetch", lambda start: [{"doi": "ax", "server": "arXiv"}])
    rows = run.fetch_recent(14)
    dois = {r["doi"] for r in rows}
    assert "bioinformatics/249" in dois  # the newest row survives: no cap
    assert not any(d.endswith("/revised") for d in dois)  # revisions are not new papers
    assert {r["server"] for r in rows} == {"biorxiv", "medrxiv", "arXiv"}
    assert "genetic and genomic medicine/0" in dois and all(r["lane"] == "in" for r in rows)


def test_rank_takes_scored_items_only():
    rows = [
        {"doi": "a", "fit_score": 0.2},
        {"doi": "b", "fit_score": None},
        {"doi": "c", "fit_score": 0.9},
    ]
    assert [r["doi"] for r in run.rank(rows, 5)] == ["c", "a"]


def test_rank_does_not_hand_every_tie_to_one_server():
    # ~9% of papers tie at exactly 0.85; a DOI tie-break gives them all to the prefix that sorts
    # first (arXiv's 10.48550 before bioRxiv's 10.64898), so the digest was all-arXiv
    rows = [
        {"doi": f"{prefix}/{i}", "server": prefix, "fit_score": 0.85}
        for prefix in ("10.48550", "10.64898")
        for i in range(100)
    ]
    assert {r["server"] for r in run.rank(rows, 10)} == {"10.48550", "10.64898"}


def test_break_ties_rescores_only_the_group_at_the_cutoff(monkeypatch):
    rows = [
        {"doi": d, "title": d, "abstract": "x", "category": "c", "lane": "in", "fit_score": f}
        for d, f in [
            ("a", 0.9),
            ("b", 0.9),
            ("t1", 0.85),
            ("t2", 0.85),
            ("t3", 0.85),
            ("t4", 0.85),
            ("t5", 0.85),
            ("z", 0.5),
        ]
    ]
    second = {"t1": 0.6, "t2": 0.95, "t3": 0.7, "t4": 0.9, "t5": 0.1}
    calls = []

    def fake(t):
        (model, *_), item, _ = t
        calls.append((model, item["doi"]))
        return {"doi": item["doi"], "fit_score": second[item["doi"]], "cost_usd": 0.0002}

    monkeypatch.setattr(run.harness, "run_one", fake)
    annotated = []
    monkeypatch.setattr(run.tiebreak, "annotate", lambda g: annotated.extend(r["doi"] for r in g))
    spent = run.break_ties(rows, 4)
    assert sorted(annotated) == ["t1", "t2", "t3", "t4", "t5"]
    assert sorted(d for _, d in calls) == ["t1", "t2", "t3", "t4", "t5"]
    assert {m for m, _ in calls} == {run.RERANK[0]}
    assert spent == pytest.approx(0.001)
    picked = [r["doi"] for r in run.rank(rows, 4)]
    assert set(picked[:2]) == {"a", "b"} and picked[2:] == ["t2", "t4"]  # rerank decides the 0.85s


def test_rank_applies_the_secondary_keys_in_order():
    tied = {"fit_score": 0.85, "tiebreak": 0.9}
    rows = [
        {"doi": "plain", **tied},
        {"doi": "similar", **tied, "similar": 0.9},
        {"doi": "data", **tied, "open_data": 1.0},
        {"doi": "inst", **tied, "top_inst": 1.0, "similar": 0.1},
    ]
    assert [r["doi"] for r in run.rank(rows, 4)] == ["inst", "data", "similar", "plain"]


def test_break_ties_spends_nothing_without_a_tie_at_the_cutoff(monkeypatch):
    rows = [{"doi": d, "fit_score": f} for d, f in [("a", 0.9), ("b", 0.8), ("c", 0.8)]]
    monkeypatch.setattr(run.harness, "run_one", lambda t: pytest.fail("no rerank needed"))
    assert run.break_ties(rows, 1) == 0 and run.break_ties(rows, 5) == 0


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
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(run, "STATE", (tmp_path / "seen.json", tmp_path / "intern.log"))
    monkeypatch.setattr(run, "fetch_recent", lambda days: [{**p, "abstract": "x"} for p in PICKS])
    monkeypatch.setattr(
        run.harness, "run_one", lambda t: {**t[1], "title": t[1]["title"][:3], "cost_usd": 5e-5}
    )
    monkeypatch.setattr(mailer, "send", lambda *a: pytest.fail("must not send"))
    assert run.main(["--dry-run", "--top", "1"]) == 0
    out = capsys.readouterr().out
    assert (
        "Preprint intern: 1 picks for" in out and "Alpha paper" in out and "Beta paper" not in out
    )
    assert not (tmp_path / "seen.json").exists()


def test_live_run_sends_and_records(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    seen_path = tmp_path / "seen.json"
    monkeypatch.setattr(run, "STATE", (seen_path, tmp_path / "intern.log"))
    monkeypatch.setattr(run, "fetch_recent", lambda days: [{**p, "abstract": "x"} for p in PICKS])
    monkeypatch.setattr(run.harness, "run_one", lambda t: {**t[1], "cost_usd": 0.00005})
    monkeypatch.setattr(credentials, "load", lambda: CREDS)
    sent = []
    monkeypatch.setattr(mailer, "send", lambda creds, digest: sent.append(digest))
    assert run.main([]) == 0
    assert len(sent) == 1 and len(sent[0].picks) == 2
    assert json.loads(seen_path.read_text())["last_sent"] == date.today().isoformat()
    assert run.main([]) == 0 and len(sent) == 1  # not due again: nothing sent
