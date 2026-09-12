"""The judge: one prompt for every model, plus the parser that decides coverage."""

from __future__ import annotations

import json
import re
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

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


def load_profile() -> str:
    return PROFILE_PATH.read_text()


def build_messages(item: dict, profile: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM.format(profile=profile)},
        {"role": "user", "content": USER.format(title=item["title"], abstract=item["abstract"])},
    ]


def reasoning_body(level: str) -> dict:
    """OpenRouter `reasoning` param (verified 2026-09-11): {"enabled": false} switches thinking
    off, {"effort": "low"|"medium"|"high"} turns it up. Omitting the key leaves it to the provider
    default, which for DeepSeek V4 Flash means ON."""
    if level == "off":
        return {"reasoning": {"enabled": False}}
    return {"reasoning": {"effort": level}}


def parse(raw: str) -> dict:
    """Strict on the score, lenient on wrapping. Anything that raises here counts as uncovered."""
    text = _FENCE.sub("", (raw or "").strip())
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"not JSON: {e}") from e
    if not isinstance(obj, dict) or "fit_score" not in obj:
        raise ValueError("no fit_score")
    try:
        score = float(obj["fit_score"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"fit_score not numeric: {obj['fit_score']!r}") from e
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"fit_score out of range: {score}")
    return {
        "fit_score": score,
        "field": str(obj.get("field", "")),
        "rationale": str(obj.get("rationale", "")),
    }
