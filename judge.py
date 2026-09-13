"""The judge: one prompt for every model, plus the parser that decides coverage.

Coverage is a property of the parser, so the parser is a ladder and every result says which
rung it needed:
  strict    the whole body was one JSON object (json.loads)
  lenient   the first JSON object in the body, fences and trailing chatter ignored
  repaired  json_repair fixed a trailing comma, a control character, a missing quote
The score itself is never repaired: a body with no numeric fit_score in [0, 1] fails on every rung.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import json_repair

PROFILE_PATH = Path(__file__).with_name("profile.md")

SYSTEM = """You triage preprints for one reader. Their reading profile is below.
Score how well the preprint fits the profile.

Return ONLY a JSON object with exactly these keys:
  "fit_score": a number from 0 to 1 (1 = must-read for this reader, 0 = unrelated)
  "field": the preprint's primary field, 1-4 words
  "rationale": at most 2 sentences

Calibration rules:
  - A preprint outside the profile's fields scores below 0.5, however good it is.
  - 0.5-0.7: in a listed field but routine. 0.8+: on a listed interest with a claim worth checking.

READING PROFILE
---------------
{profile}"""

USER = "Title: {title}\n\nAbstract: {abstract}"

_DECODER = json.JSONDecoder()


SCHEMA = {
    "type": "object",
    "properties": {
        "fit_score": {"type": "number", "minimum": 0, "maximum": 1},
        "field": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": ["fit_score", "field", "rationale"],
    "additionalProperties": False,
}


def response_format(mode: str) -> dict:
    """OpenRouter response_format. json_object is the baseline every row was run in; json_schema
    (strict) is the structured-output mode, verified live 2026-09-12 to make Haiku return bare
    JSON where json_object mode gave a fenced block 270 times out of 270."""
    if mode == "json_schema":
        return {
            "type": "json_schema",
            "json_schema": {"name": "preprint_fit", "strict": True, "schema": SCHEMA},
        }
    return {"type": "json_object"}


def load_profile() -> str:
    return PROFILE_PATH.read_text()


def build_messages(item: dict, profile: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM.format(profile=profile)},
        {"role": "user", "content": USER.format(title=item["title"], abstract=item["abstract"])},
    ]


def reasoning_body(level: str) -> dict:
    """OpenRouter `reasoning` param (verified 2026-09-11): {"enabled": false} switches thinking
    off, {"effort": "low"|"medium"|"high"} turns it up. "default" omits the key and takes the
    provider default (DeepSeek V4 Flash: ON). Gemini 3.5 Flash-Lite and GLM 5.3 Flash reject
    enabled=false with HTTP 400 "Reasoning is mandatory for this endpoint", so they run at
    default."""
    if level == "default":
        return {}
    if level == "off":
        return {"reasoning": {"enabled": False}}
    return {"reasoning": {"effort": level}}


def _first_object(raw: str) -> tuple[dict, str]:
    """The first well-formed JSON object and whatever followed it.

    Lenient on purpose: a downstream pipeline would take the first object and move on, so
    counting "valid JSON, then the model said it again" as a coverage failure would overstate
    the finding. `strict` in the parse result records whether the whole body was clean JSON.
    """
    start = raw.find("{")
    if start < 0:
        raise ValueError("no JSON object in response")
    obj, end = _DECODER.raw_decode(raw, start)
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON is not an object")
    return obj, raw[end:].strip()


def _score_of(obj: dict) -> float:
    if "fit_score" not in obj:
        raise ValueError("no fit_score")
    try:
        score = float(obj["fit_score"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"fit_score not numeric: {obj['fit_score']!r}") from e
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"fit_score out of range: {score}")
    return score


def _ladder(text: str) -> tuple[dict, str, str]:
    """(object, trailing text, tier) from the first rung that yields a JSON object."""
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj, "", "strict"
    except json.JSONDecodeError:
        pass
    try:
        obj, trailing = _first_object(text)
        return obj, trailing, "lenient"
    except (json.JSONDecodeError, ValueError):
        pass
    obj = json_repair.repair_json(text, return_objects=True)
    if not isinstance(obj, dict) or not obj:
        raise ValueError("not JSON, and not repairable into an object")
    return obj, "", "repaired"


def parse(raw: str) -> dict:
    """Strict on the score, lenient on wrapping. Anything that raises here counts as uncovered."""
    text = (raw or "").strip()
    obj, trailing, tier = _ladder(text)
    score = _score_of(obj)
    return {
        "fit_score": score,
        "field": str(obj.get("field", "")),
        "rationale": str(obj.get("rationale", "")),
        "strict_json": tier == "strict" and not trailing,
        "parse_tier": tier,
    }


def tier_of(raw: str | None) -> str | None:
    """Which rung a stored body parses on, or None. Post-hoc re-parse for the coverage ladder."""
    try:
        return parse(raw or "")["parse_tier"]
    except ValueError:
        return None


def coverage_ladder(runs: list[dict]) -> dict[str, float]:
    """% of calls parseable at or below each rung; NaN for rows that carry no raw body."""
    tiers = [r.get("parse_tier") for r in runs if "raw" in r]
    if not tiers:
        return dict.fromkeys(("cov_strict", "cov_lenient", "cov_repaired"), math.nan)
    n = len(tiers)
    strict = sum(t == "strict" for t in tiers)
    lenient = strict + sum(t == "lenient" for t in tiers)
    repaired = lenient + sum(t == "repaired" for t in tiers)
    return {
        "cov_strict": 100 * strict / n,
        "cov_lenient": 100 * lenient / n,
        "cov_repaired": 100 * repaired / n,
    }
