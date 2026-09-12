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

| metric             | meaning                                                                                            |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| **cov%**           | calls that returned a parseable 0-1 score. Timeouts, bad JSON, and empty content count against it. |
| **wrong-field**    | off-lane preprints scored >= 0.5. The profile says what is off-lane; the model should too.         |
| **sigma**          | mean per-preprint std dev across the 3 repeats. Repeatability.                                     |
| **MAE vs ceiling** | mean over preprints of \|model mean - ceiling mean\|. Agreement with the frontier model.           |
| **latency**        | mean wall-clock seconds per call.                                                                  |
| **$/call**         | mean cost per call as reported by OpenRouter, not the price sheet.                                 |

## Results

<!-- RESULTS:START -->

Run of 2026-09-11: 90 preprints x 15 model configurations x 3 repeats = 4,050 calls,
$2.19 measured, of which $1.06 was the ceiling pass.

| model                                  |  cov% | strict% | wrong-field | sigma | MAE vs ceiling | top-10 | latency s |  $/call |
| -------------------------------------- | ----: | ------: | ----------: | ----: | -------------: | -----: | --------: | ------: |
| anthropic/claude-sonnet-5              |  94.4 |    97.3 |           0 | 0.011 |          0.000 |  10/10 |      3.25 | 0.00394 |
| minimax/minimax-m3@low                 |  82.2 |   100.0 |           1 | 0.047 |          0.072 |   6/10 |      1.43 | 0.00022 |
| tencent/hy3                            | 100.0 |   100.0 |           0 | 0.033 |          0.088 |   5/10 |      4.22 | 0.00006 |
| deepseek/deepseek-v4-flash-0731@medium |  99.6 |   100.0 |           1 | 0.047 |          0.092 |   6/10 |     13.89 | 0.00013 |
| deepseek/deepseek-v4-flash-0731@low    | 100.0 |   100.0 |           1 | 0.058 |          0.096 |   6/10 |     16.77 | 0.00014 |
| minimax/minimax-m3                     |  79.6 |   100.0 |           1 | 0.046 |          0.101 |   6/10 |      1.39 | 0.00026 |
| xiaomi/mimo-v2.5                       | 100.0 |   100.0 |           2 | 0.065 |          0.103 |   6/10 |      5.55 | 0.00007 |
| qwen/qwen3.8-flash                     |  99.6 |   100.0 |           1 | 0.063 |          0.118 |   5/10 |      1.89 | 0.00010 |
| inception/mercury-2.5                  |  99.3 |    99.6 |           0 | 0.062 |          0.120 |   6/10 |      0.89 | 0.00007 |
| google/gemini-3.5-flash-lite           | 100.0 |   100.0 |           0 | 0.015 |          0.124 |   7/10 |      1.06 | 0.00044 |
| anthropic/claude-haiku-4.5             | 100.0 |     0.0 |           0 | 0.010 |          0.136 |   7/10 |      2.35 | 0.00161 |
| deepseek/deepseek-v4.1-flash           | 100.0 |   100.0 |           3 | 0.061 |          0.140 |   8/10 |      4.43 | 0.00025 |
| z-ai/glm-5.3-flash                     | 100.0 |    97.4 |           0 | 0.035 |          0.147 |   7/10 |     11.48 | 0.00050 |
| deepseek/deepseek-v4-flash-0731        | 100.0 |   100.0 |           3 | 0.081 |          0.158 |   6/10 |      4.33 | 0.00008 |
| openai/gpt-5.6-luna                    | 100.0 |   100.0 |           2 | 0.024 |          0.181 |   5/10 |      1.80 | 0.00027 |

`minimax/minimax-m3@low` has the best agreement in the table and answered 82% of the
time, so it is not usable. Among configurations at >= 99% coverage, `tencent/hy3` has
both the best agreement and the lowest price; `deepseek/deepseek-v4.1-flash` matched the
most of the ceiling's own top ten (8/10) while ranking ninth of twelve on MAE, which is
why both columns are here.

Reproduce with `uv run python analyze.py` against `data/results.jsonl`.

<!-- RESULTS:END -->

![MAE against measured cost per call](results/fig_mae_vs_cost.png)
![Coverage by model configuration](results/fig_coverage.png)

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
  so the harness always sends it. Two models refuse the off switch with HTTP 400
  "Reasoning is mandatory for this endpoint": Gemini 3.5 Flash-Lite (which then reports
  0 reasoning tokens anyway) and GLM 5.3 Flash (which does think). Those two run at
  provider default, marked `"default"` in the roster.
- **Per-call timeout is 240 s.** A judge that needs more than four minutes for one
  abstract is not a judge; timeouts count against coverage.
- **max_tokens is 4096 for every call.** Reasoning tokens are billed as completion
  tokens and count against it.
- **Cost is measured, not looked up.** `usage: {"include": true}` makes OpenRouter
  return the cost of each call; `$/call` is the mean over calls that returned.
- **The provider that served each call is recorded, and it matters.** A model id on
  OpenRouter is a routing decision, not a model: the same id is served by several
  providers and they do not all honor the same parameters. In this run one provider
  ignored `reasoning: {"enabled": false}` for MiniMax M3, emitted reasoning tokens
  and returned `content: null` on every call it served, while two others honored it
  and answered normally. `analyze.py` prints coverage per (model, provider) for
  exactly this reason. Pin `provider: {"only": [...], "allow_fallbacks": false}` if
  you need a run to be reproducible.
- **A parseable score is not clean JSON.** Claude Haiku 4.5 wrapped all 270 of its
  JSON-mode responses in a ` ```json ` markdown fence, so a bare `json.loads()`
  scores it at 0% coverage. `judge.parse` takes the first JSON object in the body and
  records `strict_json` separately; the table reports both.
- The ceiling is scored with the same 3 repeats, so its row shows its own sigma and
  how many "wrong-field" calls the ceiling itself makes.

## Caveats

You are calibrating to a model, not to truth. A cheap judge with MAE 0.05 against the
ceiling inherits every blind spot the ceiling has. The ceiling's own wrong-field count
is the only check on that in this repo, and it is a weak one. Read the post for the
longer version.

## License

MIT.
