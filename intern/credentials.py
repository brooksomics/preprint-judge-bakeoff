"""Gmail SMTP credentials for the digest, from a chmod-600 JSON file outside the repo."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("~/.preprint-judge/credentials.json").expanduser()


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
