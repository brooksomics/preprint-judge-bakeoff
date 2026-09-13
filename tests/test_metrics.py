"""Pins the metric math. If MAE, coverage, violations, or sigma change, this fails."""

import io
import json
import math
from datetime import date

import pytest

import analyze
import fetch_preprints
import judge
import report

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


def test_mae_interval_brackets_mae_and_reference_has_p_one(rows):
    m = analyze.metrics(rows, CEILING)
    assert m["m"]["mae_lo"] <= m["m"]["mae"] <= m["m"]["mae_hi"]
    assert m[CEILING]["mae_lo"] == m[CEILING]["mae_hi"] == 0.0
    # "m" is the only challenger, so it is its own reference (fallback: nothing at >= 99% cov)
    assert analyze.best_usable(m, CEILING) == "m" and m["m"]["mae_diff_p"] == 1.0
    assert m[CEILING]["mae_diff_p"] == 1.0  # the ceiling beats everything in every resample


def test_sync_readme_replaces_only_the_table(tmp_path):
    readme = tmp_path / "README.md"
    frame = "intro\n<!-- RESULTS:START -->\nprose\n{}\n\nmore\n<!-- RESULTS:END -->\ntail\n"
    readme.write_text(frame.format("| a |\n|---|\n| 1 |"))
    report.sync_readme(readme, "| b |\n|---|\n| 2 |\n")
    assert readme.read_text() == frame.format("| b |\n|---|\n| 2 |")


def test_derived_rows_get_no_mae_but_keep_rank_columns(rows, tmp_path):
    rows += [row("baseline:x", d, 0, s) for d, s in (("a", 0.1), ("b", 0.9), ("c", 0.5))]
    for r in rows:
        r.setdefault("latency_s", 0.0)
        r.setdefault("cost_usd", 0.0)
    m = analyze.metrics(rows, CEILING)
    b = m["baseline:x"]
    assert all(math.isnan(b[k]) for k in ("mae", "mae_lo", "mae_hi"))
    assert b["spearman"] == pytest.approx(-1.0) and b["top10"] >= 0  # ranks exactly reversed
    assert analyze.best_usable(m, CEILING) == "m"  # derived rows are never the reference
    report.write_tables(m, tmp_path)
    line = next(
        ln for ln in (tmp_path / "results.md").read_text().splitlines() if "baseline:x" in ln
    )
    assert "| n/a | n/a | n/a |" in line and "-1.00" in line  # sigma, MAE, P all n/a


def test_ceiling_mae_is_zero(rows):
    c = analyze.metrics(rows, CEILING)[CEILING]
    assert (
        c["mae"] == 0.0
        and c["kappa_0.5"] == 1.0
        and c["alpha_ord"] == 1.0
        and c["kappa_top10"] == 1.0
    )


def test_write_agreement_renders_band_and_verdict(tmp_path):
    table = [
        {
            "label": "m",
            "category": "all",
            "n": 9,
            "kappa_0.5": 0.7,
            "alpha_ord": 0.5,
            "verdict": "reliable",
        }
    ]
    report.write_agreement(table, tmp_path / "a.md")
    text = (tmp_path / "a.md").read_text()
    assert "| m | all | 9 | 0.70 | substantial | 0.50 | reliable |" in text and "n >= 8" in text


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
    assert got == {
        "fit_score": 0.73,
        "field": "genomics",
        "rationale": "ok",
        "strict_json": False,
        "parse_tier": "lenient",
    }


def test_parse_takes_first_object_and_flags_trailing_output():
    """Valid JSON followed by the model saying it again is covered, but not strict."""
    one = '{"fit_score": 0.4, "field": "x", "rationale": "y"}'
    assert judge.parse(one)["strict_json"] is True
    dup = judge.parse(f"{one}\n\nWait, let me redo that.\n{one}")
    assert (
        dup["fit_score"] == 0.4 and dup["strict_json"] is False and dup["parse_tier"] == "lenient"
    )


def test_parse_ladder_strict_lenient_repaired():
    clean = '{"fit_score": 0.4, "field": "x", "rationale": "y"}'
    assert judge.parse(clean)["parse_tier"] == "strict"
    assert judge.parse(f"```json\n{clean}\n```")["parse_tier"] == "lenient"
    # lifted from data/results.jsonl: a trailing comma, and an invalid control character
    comma = judge.parse('{"fit_score": 0.15, "field": "x", }')
    assert comma["fit_score"] == 0.15 and comma["parse_tier"] == "repaired"
    assert comma["strict_json"] is False
    ctrl = judge.parse('{"fit_score": 0.05, "field": "h", "rationale": "line one\x01line two"}')
    assert ctrl["parse_tier"] == "repaired" and ctrl["fit_score"] == 0.05
    # a missing quote before the next key, the Mercury 2.5 shape
    mercury = judge.parse('{"fit_score": 0.85, "field": "Population-scale, "rationale": "r"}')
    assert mercury["parse_tier"] == "repaired" and mercury["fit_score"] == 0.85


def test_parse_repair_does_not_invent_a_score():
    with pytest.raises(ValueError):
        judge.parse('{"": 0.7, "field": "spatial transcriptomics"}')  # well-formed, no fit_score
    with pytest.raises(ValueError):
        judge.parse('{"fit_score":": 0.0","field":"x"}')  # repairs to a non-numeric score


def test_tier_of_returns_none_when_nothing_parses():
    assert judge.tier_of("{}") is None and judge.tier_of("") is None and judge.tier_of(None) is None
    assert judge.tier_of('{"fit_score": 0.2}') == "strict"


def test_coverage_ladder_percentages():
    runs = [
        {"raw": "x", "parse_tier": t} for t in ("strict", "strict", "lenient", "repaired", None)
    ]
    assert judge.coverage_ladder(runs) == {
        "cov_strict": 40.0,
        "cov_lenient": 60.0,
        "cov_repaired": 80.0,
    }
    assert all(
        math.isnan(v) for v in judge.coverage_ladder([{"fit_score": 0.1}]).values()
    )  # no raw


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
    report.write_tables(m, tmp_path)
    csv = (tmp_path / "results.csv").read_text().splitlines()
    assert csv[0].startswith(
        "label,cov,strict,cov_strict,cov_lenient,cov_repaired,violations,sigma,mae,mae_lo,mae_hi,mae_diff_p,spearman,kappa_0.5,alpha_ord,kappa_top10,len_rho,top10"
    )
    assert json.dumps(m)  # serializable


def test_provider_detail_reports_only_providers_below_full_coverage():
    rows = [
        {"label": "m", "provider": "Good", "fit_score": 0.5, "reasoning_tokens": 0},
        {"label": "m", "provider": "Bad", "fit_score": None, "reasoning_tokens": 80},
        {"label": "m", "provider": "Bad", "fit_score": 0.4, "reasoning_tokens": 120},
    ]
    out = report.provider_detail(rows)
    assert out == ["m via Bad: 50.0% of 2 calls, mean 100 reasoning tok"]


def test_violation_detail_lists_off_lane_hits(rows):
    for r in rows:
        r.setdefault("category", "neuroscience")
    lines = report.violation_detail(rows)
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


def test_unpack_falls_back_to_the_reasoning_field_when_content_is_empty():
    """One provider returns the completion in message.reasoning and leaves content null."""
    import harness

    answer = '{"fit_score": 0.3, "field": "bioinformatics", "rationale": "ok"}'
    misrouted = {
        "choices": [{"message": {"content": None, "reasoning": answer}, "finish_reason": "stop"}],
        "usage": {"cost": 0.0001},
    }
    got = harness.unpack(misrouted)
    assert got["fit_score"] == 0.3 and got["content_field"] == "reasoning"

    normal = {
        "choices": [{"message": {"content": answer, "reasoning": ""}, "finish_reason": "stop"}],
        "usage": {"cost": 0.0001},
    }
    assert harness.unpack(normal)["content_field"] == "content"


def test_unpack_records_a_parse_error_when_both_fields_are_unusable():
    import harness

    resp = {"choices": [{"message": {"content": "", "reasoning": ""}}], "usage": {}}
    got = harness.unpack(resp)
    assert got.get("fit_score") is None and "parse_error" in got


def test_violations_count_calls_not_preprints(rows):
    """One off-lane preprint misjudged on both its repeats counts twice, not once."""
    m = analyze.metrics(rows, CEILING)["m"]
    off = [r for r in rows if r["label"] == "m" and r["lane"] == "off"]
    assert len({r["doi"] for r in off}) == 1 and m["violations"] == 2
