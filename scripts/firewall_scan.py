"""Block private terms and secret-shaped text from reaching a public repo.

Stdlib only. The denylist itself is PRIVATE and never lives in the repo: it is read
from $FIREWALL_TERMS or ~/.config/firewall/terms.txt (one case-insensitive regex per
line, '#' comments). Without it the scanner still runs the generic built-in checks and
warns loudly; pass --require-terms (the local pre-commit wrapper does) to fail instead.

Output: file:line:rule:excerpt, exit 1 on any hit. --history scans `git log -p`.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_TERMS = Path.home() / ".config" / "firewall" / "terms.txt"
TEXT_EXT = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".jsonl", ".csv"}
TEXT_EXT |= {".txt", ".example", ".cfg"}
# Preprint text legitimately contains words like "recruitment"; scan the other values.
EXEMPT_KEYS = {"title", "abstract", "rationale", "raw", "field"}
DATA_FILES = {"data/preprints.json", "data/results.jsonl"}
GENERIC = {
    "home-path": re.compile(r"(?<![\w.])/(?:Users|home)/[\w.-]+"),
    "email": re.compile(
        r"(?<![\w.+-])(?!no-?reply@)\w[\w.+-]*@"
        r"(?![\w.-]*noreply\.github\.com\b)(?!example\.)[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"
    ),
    "key-assignment": re.compile(
        r"(?i)(?:key|token|secret|password)\w*\s*[=:]\s*[\"']?[A-Za-z0-9_\-/+]{16,}"
    ),
}


def load_terms(path):
    """Compile the private denylist: {"term1": pattern, ...}. Never echo the terms."""
    lines = Path(path).read_text().splitlines()
    patterns = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    return {f"term{i}": re.compile(p, re.IGNORECASE) for i, p in enumerate(patterns, 1)}


def build_rules(terms_path, require):
    """Generic rules plus the denylist; missing denylist warns, or exits 2 with require."""
    path = Path(terms_path)
    if path.is_file():
        return {**GENERIC, **load_terms(path)}
    if require:
        print(f"firewall_scan: denylist missing at {path}; refusing to run", file=sys.stderr)
        raise SystemExit(2)
    print(f"firewall_scan: WARNING no denylist at {path}; generic checks only", file=sys.stderr)
    return dict(GENERIC)


def redact(line, m):
    """40-char excerpt around the match, with the matched text masked past 3 chars."""
    masked = m.group(0)[:3] + "*" * min(len(m.group(0)) - 3, 6)
    start = max(0, m.start() - 12)
    return (line[start : m.start()] + masked + line[m.end() :])[:40]


def scan_lines(lines, rules):
    """Return [(lineno, rule, excerpt)] for every rule that matches a line."""
    return [
        (n, name, redact(line, m))
        for n, line in enumerate(lines, 1)
        for name, pat in rules.items()
        if (m := pat.search(line))
    ]


def data_lines(path):
    """One text line per record with EXEMPT_KEYS removed; .json list or .jsonl."""
    text = Path(path).read_text()
    records = (
        json.loads(text)
        if path.suffix == ".json"
        else [json.loads(ln) for ln in text.splitlines() if ln.strip()]
    )
    return [json.dumps({k: v for k, v in r.items() if k not in EXEMPT_KEYS}) for r in records]


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True, text=True)
    return [Path(p) for p in out.stdout.split("\0") if p and Path(p).suffix in TEXT_EXT]


def file_lines(path):
    if path.as_posix() in DATA_FILES:
        return data_lines(path)
    return path.read_text(errors="replace").splitlines()


def history_lines():
    # ponytail: data files are exempt-field JSON; the tree scan covers their other values
    cmd = ["git", "log", "-p", "--", ".", *(f":(exclude){f}" for f in sorted(DATA_FILES))]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out.stdout.splitlines()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--require-terms", action="store_true", help="fail if the denylist is missing")
    ap.add_argument("--history", action="store_true", help="scan `git log -p` instead of the tree")
    args = ap.parse_args(argv)
    rules = build_rules(os.environ.get("FIREWALL_TERMS", DEFAULT_TERMS), args.require_terms)
    targets = (
        [(Path("<history>"), history_lines())]
        if args.history
        else [(p, file_lines(p)) for p in tracked_files()]
    )
    hits = [(p, *h) for p, lines in targets for h in scan_lines(lines, rules)]
    for p, n, rule, excerpt in hits:
        print(f"{p}:{n}:{rule}:{excerpt}")
    print(f"firewall_scan: {len(hits)} hit(s) across {len(targets)} target(s)", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
