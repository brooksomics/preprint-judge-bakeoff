"""Credentials for the intern, from one chmod-600 JSON file outside the repo.

Gmail for the digest, and optionally the OpenRouter key: an interactive run exports that key
or sources `.env`, but a launchd agent has no shell to do either, so it may live here instead.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("~/.preprint-judge/credentials.json").expanduser()
OPENROUTER_ENV = "OPENROUTER_API_KEY"


@dataclass(frozen=True)
class Gmail:
    sender: str
    app_password: str
    receiver: str


def load(path: Path = DEFAULT_PATH) -> Gmail:
    """Shape: {"gmail": {"sender": ..., "app_password": ...}, "receiver": ...}."""
    if not path.exists():
        raise FileNotFoundError(f"no credentials at {path}; see credentials.json.example")
    raw = json.loads(path.read_text())
    try:
        gmail = raw["gmail"]
        return Gmail(str(gmail["sender"]), str(gmail["app_password"]), str(raw["receiver"]))
    except (KeyError, TypeError) as e:
        raise ValueError(f"credentials.json is missing {e}; see credentials.json.example") from e


def ensure_api_key(path: Path = DEFAULT_PATH) -> None:
    """Put the OpenRouter key in the environment, where harness.py reads it on every call.

    An exported key always wins, so interactive runs are unaffected; otherwise it comes from
    `openrouter_api_key` in the credentials file. Raises if neither has it.
    """
    if os.environ.get(OPENROUTER_ENV, "").strip():
        return
    raw = json.loads(path.read_text()) if path.exists() else {}
    key = str(raw.get("openrouter_api_key", "")).strip()
    if not key:
        raise RuntimeError(f"no {OPENROUTER_ENV} exported and no openrouter_api_key in {path}")
    os.environ[OPENROUTER_ENV] = key
