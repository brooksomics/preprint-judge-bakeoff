"""The judge: one prompt for every model, plus the parser that decides coverage."""

from __future__ import annotations

import json
from pathlib import Path

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


def parse(raw: str) -> dict:
    """Strict on the score, lenient on wrapping. Anything that raises here counts as uncovered."""
    text = (raw or "").strip()
    try:
        obj, trailing = _first_object(text)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"not JSON: {e}") from e
    score = _score_of(obj)
    return {
        "fit_score": score,
        "field": str(obj.get("field", "")),
        "rationale": str(obj.get("rationale", "")),
        "strict_json": not trailing and text.startswith("{"),
    }
