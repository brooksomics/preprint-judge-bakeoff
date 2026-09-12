"""Pins the metric math. If MAE, coverage, violations, or sigma change, this fails."""

import io
import json
from datetime import date

import pytest

import analyze
import fetch_preprints
import judge

CEILING = "ceiling/model"


def row(label, doi, run, score, lane="in", **kw):
    return {"label": label, "doi": doi, "run_idx": run, "fit_score": score, "lane": lane, **kw}


@pytest.fixture
def rows():
    return [
        # ceiling: item a mean 0.8, item b mean 0.2, item c mean 0.5
        row(CEILING, "a", 0, 0.9),
        row(CEILING, "a", 1, 0.7),
        row(CEILING, "a", 2, 0.8),
        row(CEILING, "b", 0, 0.2, lane="off"),
        row(CEILING, "b", 1, 0.2, lane="off"),
        row(CEILING, "c", 0, 0.5),
        # challenger: a mean 0.6 (|0.6-0.8|=0.2), b mean 0.6 (0.4, violation x2), c unparsed
        row("m", "a", 0, 0.5),
        row("m", "a", 1, 0.7),
        row("m", "b", 0, 0.6, lane="off"),
        row("m", "b", 1, 0.6, lane="off"),
        row("m", "c", 0, None),
        row("m", "c", 1, None),
        # latency / cost carried on every row
    ]


def test_mae_vs_ceiling_is_mean_abs_diff_of_item_means(rows):
    m = analyze.metrics(rows, CEILING)["m"]
    assert m["mae"] == pytest.approx((0.2 + 0.4) / 2)  # item c has no score -> excluded


def test_ceiling_mae_is_zero(rows):
    assert analyze.metrics(rows, CEILING)[CEILING]["mae"] == 0.0


def test_shortlist_takes_top_n_and_breaks_ties_by_doi():
    means = {"a": 0.9, "b": 0.5, "c": 0.5, "d": 0.1}
    assert analyze.shortlist(means, 3) == {"a", "b", "c"}
    assert analyze.shortlist(means, 2) == {"a", "b"}  # b before c on DOI order


def test_top10_counts_overlap_with_the_ceilings_shortlist(rows, monkeypatch):
    """Ceiling ranks a > c > b; the challenger ranks b = a > c, so a top-2 overlaps on a."""
    monkeypatch.setattr(analyze, "SHORTLIST", 2)
    m = analyze.metrics(rows, CEILING)
    assert m[CEILING]["top10"] == 2
    assert m["m"]["top10"] == 1


def test_coverage_counts_parseable_scores(rows):
    m = analyze.metrics(rows, CEILING)["m"]
    assert m["cov"] == pytest.approx(100 * 4 / 6)


def test_strict_is_share_of_covered_calls_with_clean_json(rows):
    for i, r in enumerate(r for r in rows if r["label"] == "m" and r["fit_score"] is not None):
        r["strict_json"] = i < 3  # 3 of the 4 covered calls were clean JSON
    assert analyze.metrics(rows, CEILING)["m"]["strict"] == pytest.approx(75.0)


def test_wrong_field_violation_is_off_lane_scored_at_least_half(rows):
    m = analyze.metrics(rows, CEILING)
    assert m["m"]["violations"] == 2
    assert m[CEILING]["violations"] == 0


def test_sigma_is_mean_of_per_item_stdev(rows):
    m = analyze.metrics(rows, CEILING)["m"]
    # item a: stdev(0.5,0.7)=0.1414; item b: stdev(0.6,0.6)=0
    assert m["sigma"] == pytest.approx((0.14142135 + 0.0) / 2, abs=1e-6)


def test_parse_accepts_fenced_json_and_clamps_nothing():
    raw = '```json\n{"fit_score": 0.73, "field": "genomics", "rationale": "ok"}\n```'
    got = judge.parse(raw)
    assert got == {"fit_score": 0.73, "field": "genomics", "rationale": "ok", "strict_json": False}


def test_parse_takes_first_object_and_flags_trailing_output():
    """Valid JSON followed by the model saying it again is covered, but not strict."""
    one = '{"fit_score": 0.4, "field": "x", "rationale": "y"}'
    assert judge.parse(one)["strict_json"] is True
    dup = judge.parse(f"{one}\n\nWait, let me redo that.\n{one}")
    assert dup["fit_score"] == 0.4 and dup["strict_json"] is False


def test_parse_rejects_trailing_comma_which_is_not_json():
    with pytest.raises(ValueError):
        judge.parse('{"fit_score": 0.15, "field": "x", }')


@pytest.mark.parametrize("raw", ["not json", '{"field": "x"}', '{"fit_score": 1.7}', "", "[1, 2]"])
def test_parse_rejects_missing_or_out_of_range_score(raw):
    with pytest.raises(ValueError):
        judge.parse(raw)


def test_build_messages_embeds_profile_title_abstract():
    item = {"title": "T1", "abstract": "A1", "doi": "d"}
    msgs = judge.build_messages(item, "PROFILE TEXT")
    assert msgs[0]["role"] == "system" and "PROFILE TEXT" in msgs[0]["content"]
    assert "T1" in msgs[1]["content"] and "A1" in msgs[1]["content"]


def test_stratify_round_robins_across_categories_and_dedupes_doi():
    items = [
        {"doi": "1", "category": "bioinformatics", "version": "1"},
        {"doi": "1", "category": "bioinformatics", "version": "2"},  # dup
        {"doi": "2", "category": "bioinformatics", "version": "1"},
        {"doi": "3", "category": "genomics", "version": "1"},
        {"doi": "4", "category": "neuroscience", "version": "1"},
        {"doi": "5", "category": "plant biology", "version": "1"},
    ]
    picked = fetch_preprints.stratify(items, {"bioinformatics", "genomics"}, 3)
    assert [p["doi"] for p in picked] == ["1", "3", "2"]
    assert all(p["lane"] == "in" for p in picked)
    off = fetch_preprints.stratify(items, {"neuroscience", "plant biology"}, 5)
    assert len(off) == 2 and all(p["lane"] == "off" for p in off)


def test_reasoning_body_shapes():
    assert judge.reasoning_body("off") == {"reasoning": {"enabled": False}}
    assert judge.reasoning_body("low") == {"reasoning": {"effort": "low"}}
    assert judge.reasoning_body("default") == {}


def test_results_table_roundtrip(tmp_path, rows):
    for r in rows:
        r.setdefault("latency_s", 1.0)
        r.setdefault("cost_usd", 0.001)
    m = analyze.metrics(rows, CEILING)
    analyze.write_tables(m, tmp_path)
    csv = (tmp_path / "results.csv").read_text().splitlines()
    assert csv[0].startswith("label,cov,strict,violations,sigma,mae,top10,latency_s,cost_usd")
    assert json.dumps(m)  # serializable


def test_load_rows_attaches_lane_from_preprints(tmp_path):
    (tmp_path / "p.json").write_text(json.dumps([{"doi": "x", "lane": "off"}]))
    r = {"label": "m", "doi": "x", "run_idx": 0, "fit_score": 0.9}
    (tmp_path / "r.jsonl").write_text(json.dumps(r) + "\n\n")
    assert analyze.load_rows(tmp_path / "r.jsonl", tmp_path / "p.json") == [{**r, "lane": "off"}]


def test_violation_detail_lists_off_lane_hits(rows):
    for r in rows:
        r.setdefault("category", "neuroscience")
    lines = analyze.violation_detail(rows)
    assert len(lines) == 2 and all(line.startswith("m: ") for line in lines)


def test_fetch_category_pages_until_total(monkeypatch):
    def page(lo, hi):
        return {
            "messages": [{"status": "ok", "total": "35"}],
            "collection": [{"doi": str(i)} for i in range(lo, hi)],
        }

    pages, calls = {0: page(0, 30), 30: page(30, 35)}, []

    def fake_get(url):
        calls.append(url)
        return pages[int(url.rsplit("/", 1)[1].split("?")[0])]

    monkeypatch.setattr(fetch_preprints, "_get", fake_get)
    window = (date(2026, 9, 1), date(2026, 9, 10))
    rows = fetch_preprints.fetch_category("plant biology", window, 100)
    assert len(rows) == 35 and len(calls) == 2 and "category=plant_biology" in calls[0]
    assert len(fetch_preprints.fetch_category("plant biology", window, 10)) == 10


class _Resp:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return io.StringIO(json.dumps(self.body))

    def __exit__(self, *a):
        return False


def test_get_retries_on_timeout_and_raises_on_bad_status(monkeypatch):
    attempts = []

    def flaky(url, timeout):
        attempts.append(url)
        if len(attempts) == 1:
            raise TimeoutError
        return _Resp({"messages": [{"status": "ok", "total": "0"}], "collection": []})

    monkeypatch.setattr(fetch_preprints.urllib.request, "urlopen", flaky)
    monkeypatch.setattr(fetch_preprints.time, "sleep", lambda s: None)
    assert fetch_preprints._get("u")["collection"] == [] and len(attempts) == 2
    bad = _Resp({"messages": [{"status": "error"}]})
    monkeypatch.setattr(fetch_preprints.urllib.request, "urlopen", lambda url, timeout: bad)
    with pytest.raises(RuntimeError):
        fetch_preprints._get("u")


def test_figures_write_two_pngs(tmp_path, rows):
    for r in rows:
        r.setdefault("latency_s", 1.0)
        r.setdefault("cost_usd", 0.001)
    import figures

    figures.plot_all(analyze.metrics(rows, CEILING), tmp_path, CEILING)
    assert (tmp_path / "fig_mae_vs_cost.png").exists() and (tmp_path / "fig_coverage.png").exists()
