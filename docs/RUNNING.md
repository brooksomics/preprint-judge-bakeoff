# Running, re-running, and adapting

## Run the bakeoff

```bash
uv sync
export OPENROUTER_API_KEY=...            # or put it in .env and `set -a; source .env`

uv run python fetch_preprints.py         # ~1-3 min; bioRxiv paginates slowly
uv run python harness.py --smoke         # 2 preprints x 1 repeat per model: check every id resolves
uv run python harness.py                 # the full run, resumable; stops starting new configs past --budget
uv run python analyze.py                 # table + figures into results/
uv run pytest                            # pins the metric math
pre-commit install --hook-type pre-commit --hook-type pre-push   # ruff, gitleaks, firewall scan
```

The harness appends one JSON row per call and skips `(model, doi, repeat)` triples that
already exist, so a crashed or budget-stopped run picks up where it left off.

## Re-running

The model roster rots: ids get deprecated, providers change, a cheap model gets quietly
swapped. When you re-run the harness, `gate.py` says whether the production model is still fit
to ship, with one PASS/FAIL line per check and exit code 0 or 1:

```bash
uv run python gate.py --model tencent/hy3 --min-cov 99 --max-mae-hi 0.12 --min-top10 5 --max-violations 2
```

It reads `results/results.csv` (coverage, the *upper* end of the MAE interval, top-10 overlap,
wrong-field calls) and makes one GET to `https://openrouter.ai/api/v1/models` to confirm the id
still exists, so a dead id fails loudly instead of routing to whatever OpenRouter substitutes.
Thresholds are yours to set; the defaults above are the ones the current winner clears.

## Point it at your own profile

1. Edit `profile.md`. Say what you read, what you skip, and why. ~200 words is plenty.
2. Edit `IN_LANE` / `OFF_LANE` in `fetch_preprints.py` to bioRxiv categories that match.
   Off-lane papers give the wrong-field metric teeth: keep some. Clinical reader? The same
   API serves medRxiv: `uv run python fetch_preprints.py --server medrxiv` uses the
   `MED_IN_LANE` / `MED_OFF_LANE` sets and writes `data/preprints_medrxiv.json`, leaving the
   published bioRxiv set untouched; point `harness.py` and `analyze.py` at it with
   `--preprints`.
3. Edit `MODELS` in `harness.py`. Check ids against `https://openrouter.ai/api/v1/models`
   first; the roster here was verified 2026-09-11.
