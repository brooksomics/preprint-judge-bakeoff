"""Pins the firewall scanner: denylist matcher, generic checks, data-field exemptions."""

import json

import pytest

from scripts import firewall_scan as fw

# Fake denylist: no real forbidden term appears in this file.
FAKE_TERMS = "# comment line\nzebra\\s+corp\n\nsecretproject\n"


@pytest.fixture
def terms_file(tmp_path):
    p = tmp_path / "terms.txt"
    p.write_text(FAKE_TERMS)
    return p


def test_load_terms_skips_comments_and_blanks(terms_file):
    rules = fw.load_terms(terms_file)
    assert list(rules) == ["term1", "term2"]
    assert rules["term1"].search("ZEBRA   Corp")  # case-insensitive, regex honored


def test_scan_lines_reports_file_line_rule_and_redacted_excerpt(terms_file):
    rules = {**fw.GENERIC, **fw.load_terms(terms_file)}
    hits = fw.scan_lines(["fine line", "we shipped SecretProject last week"], rules)
    assert len(hits) == 1
    lineno, rule, excerpt = hits[0]
    assert (lineno, rule) == (2, "term2")
    assert "SecretProject" not in excerpt and len(excerpt) <= 40


# Bad fixtures are assembled at runtime so the scanner never sees the literal in this file.
HOME = "/" + "Users/someone/Documents/x.py"
HOME2 = "/" + "home/someone/x.py"
MAIL = "bob@" + "corp.io"
KEY = 'api_key = "' + "abcdefghijklmnopqrstuvwxyz0123" + '"'
TOKEN = "token: " + "ghp_abcdefghijklmnopqrstuvwxyz"


@pytest.mark.parametrize(
    "line,rule",
    [
        (f"see {HOME}", "home-path"),
        (f"see {HOME2}", "home-path"),
        (f"mail {MAIL} today", "email"),
        (KEY, "key-assignment"),
        (TOKEN, "key-assignment"),
    ],
)
def test_generic_rules_hit(line, rule):
    assert [h[1] for h in fw.scan_lines([line], fw.GENERIC)] == [rule]


@pytest.mark.parametrize(
    "line",
    [
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "123+me@users.noreply.github.com",
        "contact me@example.com or me@example.org",
        'key = os.environ["OPENROUTER_API_KEY"]',
        "export OPENROUTER_API_KEY=...",
        "GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}",
        "path is ./Users/relative",
        "      - uses: actions/checkout@v7.0.1",
        "  uses: astral-sh/setup-uv@v10.1.0",
        '+@pytest.mark.parametrize("raw", ["not json"])',
    ],
)
def test_generic_rules_do_not_hit(line):
    assert fw.scan_lines([line], fw.GENERIC) == []


def test_data_lines_drop_exempt_fields_only(tmp_path):
    row = {"abstract": "recruitment of zebra corp", "provider": "zebra corp", "title": "x"}
    jsonl = tmp_path / "results.jsonl"
    jsonl.write_text(json.dumps(row) + "\n" + json.dumps({"abstract": "zebra corp"}) + "\n")
    lines = fw.data_lines(jsonl)
    assert len(lines) == 2
    assert "zebra corp" in lines[0] and "recruitment" not in lines[0]
    assert "zebra" not in lines[1]

    listed = tmp_path / "preprints.json"
    listed.write_text(json.dumps([row, {"abstract": "zebra corp"}]))
    assert fw.data_lines(listed) == lines


def test_build_rules_generic_only_when_denylist_missing(tmp_path, capsys):
    rules = fw.build_rules(tmp_path / "missing.txt", require=False)
    assert set(rules) == set(fw.GENERIC)
    assert "WARNING" in capsys.readouterr().err


def test_build_rules_requires_denylist_when_asked(tmp_path):
    with pytest.raises(SystemExit) as e:
        fw.build_rules(tmp_path / "missing.txt", require=True)
    assert e.value.code == 2


def test_main_exits_1_on_hit_and_0_when_clean(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    bad = tmp_path / "notes.md"
    bad.write_text("we talked to zebra corp\n")
    monkeypatch.setattr(fw, "tracked_files", lambda: [bad])
    terms = tmp_path / "terms.txt"
    terms.write_text(FAKE_TERMS)
    monkeypatch.setenv("FIREWALL_TERMS", str(terms))
    assert fw.main([]) == 1
    assert "notes.md:1:term1:" in capsys.readouterr().out
    bad.write_text("all clear\n")
    assert fw.main([]) == 0


def test_history_lines_excludes_data_files(monkeypatch):
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        return type("R", (), {"stdout": "a\nb\n"})()

    monkeypatch.setattr(fw.subprocess, "run", fake_run)
    assert fw.history_lines() == ["a", "b"]
    assert seen["cmd"][:3] == ["git", "log", "-p"]
    assert all(f":(exclude){f}" in seen["cmd"] for f in fw.DATA_FILES)
