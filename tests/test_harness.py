"""Pins the request body the harness sends, including the json_schema strict mode."""

import harness
import judge


def test_response_format_shapes():
    assert judge.response_format("json_object") == {"type": "json_object"}
    rf = judge.response_format("json_schema")
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert set(schema["required"]) == {"fit_score", "field", "rationale"}
    assert schema["additionalProperties"] is False
    assert schema["properties"]["fit_score"] == {"type": "number", "minimum": 0, "maximum": 1}


def test_label_of_marks_reasoning_and_schema():
    assert harness.label_of("a/b", "off") == "a/b"
    assert harness.label_of("a/b", "low") == "a/b@low"
    assert harness.label_of("a/b", "off", "json_schema") == "a/b#schema"
    assert harness.label_of("a/b", "low", "json_schema") == "a/b@low#schema"


def test_run_one_body_and_row_for_schema_mode(monkeypatch):
    sent = {}

    def fake_post(body):
        sent.update(body)
        return {
            "choices": [
                {"message": {"content": '{"fit_score": 0.5, "field": "f", "rationale": "r"}'}}
            ],
            "usage": {"cost": 0.001},
        }, None

    monkeypatch.setattr(harness, "_post", fake_post)
    item = {"doi": "d", "category": "c", "lane": "in", "title": "T", "abstract": "A"}
    row = harness.run_one((("m/x", "off", "json_schema"), item, 0))
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["reasoning"] == {"enabled": False} and sent["model"] == "m/x"
    assert row["label"] == "m/x#schema" and row["mode"] == "json_schema"
    assert row["fit_score"] == 0.5 and row["parse_tier"] == "strict"
    # two-field configs still work and default to json_object
    row2 = harness.run_one((("m/x", "off"), item, 0))
    assert sent["response_format"] == {"type": "json_object"} and row2["mode"] == "json_object"


def test_roster_has_the_three_schema_reruns():
    schema_rows = [c for c in harness.MODELS if len(c) == 3 and c[2] == "json_schema"]
    assert {c[0] for c in schema_rows} == {
        "anthropic/claude-haiku-4.5",
        "z-ai/glm-5.3-flash",
        "inception/mercury-2.5",
    }
