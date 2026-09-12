"""Run every preprint through every model config via OpenRouter; append one JSON row per call.

Verified 2026-09-11 against POST https://openrouter.ai/api/v1/chat/completions:
  response_format={"type": "json_object"}   JSON mode
  reasoning={"enabled": false}              thinking off; {"effort": "low"|"medium"} turns it up
  usage={"include": true}                   returns usage.cost (USD),
                                            usage.completion_tokens_details.reasoning_tokens,
                                            and the top-level `provider` that served the call
A 200 can still carry {"error": {...}} instead of choices; that is recorded as an error row.
Resumable: (label, doi, run_idx) already present in the results file are skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import judge

URL = "https://openrouter.ai/api/v1/chat/completions"
CEILING = "anthropic/claude-sonnet-5"
# (model id, reasoning). "off" sends {"enabled": false}; "low"/"medium" send {"effort": ...}.
MODELS = [
    (CEILING, "off"),
    ("anthropic/claude-haiku-4.5", "off"),
    ("minimax/minimax-m3", "off"),
    ("minimax/minimax-m3", "low"),
    ("xiaomi/mimo-v2.5", "off"),
    ("google/gemini-3.5-flash-lite", "off"),
    ("deepseek/deepseek-v4-flash-0731", "off"),
    ("deepseek/deepseek-v4-flash-0731", "low"),
    ("deepseek/deepseek-v4-flash-0731", "medium"),
    ("tencent/hy3", "off"),
    ("openai/gpt-5.6-luna", "off"),
    # released after the August roster (OpenRouter catalog scan 2026-09-11)
    ("deepseek/deepseek-v4.1-flash", "off"),
    ("qwen/qwen3.8-flash", "off"),
    ("z-ai/glm-5.3-flash", "off"),
    ("inception/mercury-2.5", "off"),
]
MAX_TOKENS = 4096
TIMEOUT_S = (
    240  # a judge that needs >4 min for one abstract is not a judge; timeouts count as uncovered
)
RETRY_ON = {429, 500, 502, 503}
PROFILE = judge.load_profile()


def label_of(model: str, level: str) -> str:
    return model if level == "off" else f"{model}@{level}"


def _post_once(req: urllib.request.Request) -> tuple[dict | None, str | None, bool]:
    """(response, error, retryable)."""
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            return json.load(r), None, False
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read()[:200]!r}", e.code in RETRY_ON
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return None, f"{type(e).__name__}: {e}"[:300], False


def _post(body: dict) -> tuple[dict | None, str | None]:
    headers = {
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers)
    resp, err, retry = _post_once(req)
    if retry:
        time.sleep(5)
        resp, err, _ = _post_once(req)
    return resp, err


def unpack(resp: dict) -> dict:
    u = resp.get("usage") or {}
    choice = (resp.get("choices") or [{}])[0]
    raw = (choice.get("message") or {}).get("content") or ""
    out = {
        "raw": raw[:500],
        "provider": resp.get("provider"),
        "finish_reason": choice.get("finish_reason"),
        "cost_usd": u.get("cost"),
        "prompt_tokens": u.get("prompt_tokens"),
        "completion_tokens": u.get("completion_tokens"),
        "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "error": json.dumps(resp["error"])[:300] if resp.get("error") else None,
    }
    try:
        out.update(judge.parse(raw))
    except ValueError as e:
        out["parse_error"] = str(e)[:200]
    return out


def run_one(task: tuple) -> dict:
    (model, level), item, run_idx = task
    body = {
        "model": model,
        "messages": judge.build_messages(item, PROFILE),
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
        "usage": {"include": True},
        **judge.reasoning_body(level),
    }
    t0 = time.time()
    resp, err = _post(body)
    res = unpack(resp) if resp else {"error": err}
    meta = {"label": label_of(model, level), "model": model, "reasoning": level}
    item_meta = {k: item[k] for k in ("doi", "category", "lane")} | {"title": item["title"][:120]}
    return meta | item_meta | {"run_idx": run_idx, "latency_s": round(time.time() - t0, 2)} | res


def done_keys(out: Path) -> set[tuple]:
    if not out.exists():
        return set()
    rows = (json.loads(ln) for ln in out.read_text().splitlines() if ln.strip())
    return {(r["label"], r["doi"], r["run_idx"]) for r in rows}


def _results(tasks: list[tuple], workers: int):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(run_one, t) for t in tasks]
        yield from (f.result() for f in as_completed(futs))


def run_config(cfg: tuple, items: list[dict], a: argparse.Namespace) -> float:
    label, done, spent, errs = label_of(*cfg), done_keys(a.out), 0.0, 0
    tasks = [
        (cfg, it, i) for it in items for i in range(a.repeats) if (label, it["doi"], i) not in done
    ]
    print(f"=== {label}: {len(tasks)} calls ===", flush=True)
    if a.dry_run or not tasks:
        return 0.0
    with a.out.open("a") as f:
        for n, row in enumerate(_results(tasks, a.workers), 1):
            f.write(json.dumps(row) + "\n")
            f.flush()
            spent += row.get("cost_usd") or 0.0
            errs += row.get("fit_score") is None
            done = n % 25 == 0 or n == len(tasks)
            print(
                f"  {label}: {n}/{len(tasks)}  ${spent:.3f}  uncovered={errs}", flush=True
            ) if done else None
    return spent


def _select(a: argparse.Namespace) -> tuple[list[dict], list[tuple]]:
    items = json.loads(a.preprints.read_text())
    if a.smoke:
        items, a.repeats, a.out = items[:1] + items[-1:], 1, a.out.with_name("smoke.jsonl")
    wanted = [s for s in a.models.split(",") if s]
    configs = [c for c in MODELS if not wanted or any(w in label_of(*c) for w in wanted)]
    return items, configs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preprints", type=Path, default=Path("data/preprints.json"))
    ap.add_argument("--out", type=Path, default=Path("data/results.jsonl"))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--budget", type=float, default=10.0, help="stop starting new configs past $N")
    ap.add_argument("--models", default="", help="comma-separated substrings; empty = all")
    ap.add_argument("--smoke", action="store_true", help="2 preprints x 1 repeat per config")
    ap.add_argument("--dry-run", action="store_true", help="count pending calls only")
    a = ap.parse_args()
    items, configs = _select(a)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    spent = 0.0
    for cfg in configs:
        if spent > a.budget:
            print(f"budget ${a.budget} exceeded (${spent:.2f}); stopping before {label_of(*cfg)}")
            break
        spent += run_config(cfg, items, a)
    print(f"total measured spend this run: ${spent:.3f}")


if __name__ == "__main__":
    main()
