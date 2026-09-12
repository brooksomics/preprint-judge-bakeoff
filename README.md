# preprint-judge-bakeoff

Which cheap LLM can triage preprints the way a frontier model would, and how do you know?

This repo scores ~90 recent bioRxiv preprints against a personal **reading profile**
with a dozen models via [OpenRouter](https://openrouter.ai), three repeats each, and
grades every cheap model by how closely it agrees with a frontier **ceiling** model
(Claude Sonnet 5). No human labels: the ceiling is the reference, and the question is
which $0.001 model tracks it.

It is the intern that does the abstract skim for
[Journal Safari](https://www.bubbabrooks.info/blog/tag/journal-safari/), and the
write-up is
[Calibrating a Cheap LLM Judge Against a Frontier Ceiling](https://www.bubbabrooks.info/blog/llm-judge-frontier-ceiling/).

## What it does

```
fetch_preprints.py   bioRxiv API -> data/preprints.json (60 in-lane, 30 deliberately off-lane)
judge.py             the one prompt every model sees, and the parser that decides coverage
harness.py           preprints x models x 3 repeats through OpenRouter JSON mode -> data/results.jsonl
analyze.py           metrics table (results/results.md + .csv) and two figures
```

Metrics, per model config:

| metric | meaning |
|---|---|
| **cov%** | calls that returned a parseable 0-1 score. Timeouts, bad JSON, and empty content count against it. |
| **wrong-field** | off-lane preprints scored >= 0.5. The profile says what is off-lane; the model should too. |
| **sigma** | mean per-preprint std dev across the 3 repeats. Repeatability. |
| **MAE vs ceiling** | mean over preprints of \|model mean - ceiling mean\|. Agreement with the frontier model. |
| **latency** | mean wall-clock seconds per call. |
| **$/call** | mean cost per call as reported by OpenRouter, not the price sheet. |

## Results

<!-- RESULTS:START -->
_Run pending._
<!-- RESULTS:END -->

![MAE vs cost](results/fig_mae_vs_cost.png)
![Coverage](results/fig_coverage.png)

## Run it

```bash
uv sync
export OPENROUTER_API_KEY=...            # or put it in .env and `set -a; source .env`

uv run python fetch_preprints.py         # ~1-3 min; bioRxiv paginates slowly
uv run python harness.py --smoke         # 2 preprints x 1 repeat per model: check every id resolves
uv run python harness.py                 # the full run, resumable; stops starting new configs past --budget
uv run python analyze.py                 # table + figures into results/
uv run pytest                            # pins the metric math
```

The harness appends one JSON row per call and skips `(model, doi, repeat)` triples that
already exist, so a crashed or budget-stopped run picks up where it left off.

## Point it at your own profile

1. Edit `profile.md`. Say what you read, what you skip, and why. ~200 words is plenty.
2. Edit `IN_LANE` / `OFF_LANE` in `fetch_preprints.py` to bioRxiv categories that match.
   Off-lane papers give the wrong-field metric teeth: keep some.
3. Edit `MODELS` in `harness.py`. Check ids against `https://openrouter.ai/api/v1/models`
   first; the roster here was verified 2026-09-11.

## Method notes

- **Same prompt for every model** (`judge.SYSTEM`): profile + title + abstract in, JSON
  `{fit_score, field, rationale}` out via `response_format={"type": "json_object"}`.
- **Reasoning is off unless the row says otherwise.** OpenRouter's `reasoning`
  parameter: `{"enabled": false}` switches thinking off; `{"effort": "low"|"medium"}`
  turns it up. Some models (DeepSeek V4 Flash) default to ON when the key is omitted,
  so the harness always sends it.
- **Per-call timeout is 240 s.** A judge that needs more than four minutes for one
  abstract is not a judge; timeouts count against coverage.
- **max_tokens is 4096 for every call.** Reasoning tokens are billed as completion
  tokens and count against it.
- **Cost is measured, not looked up.** `usage: {"include": true}` makes OpenRouter
  return the cost of each call; `$/call` is the mean over calls that returned. The
  provider that served each call is recorded too, since the same model id can route
  to providers with different prices.
- The ceiling is scored with the same 3 repeats, so its row shows its own sigma and
  how many "wrong-field" calls the ceiling itself makes.

## Caveats

You are calibrating to a model, not to truth. A cheap judge with MAE 0.05 against the
ceiling inherits every blind spot the ceiling has. The ceiling's own wrong-field count
is the only check on that in this repo, and it is a weak one. Read the post for the
longer version.

## License

MIT.
