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
fetch_preprints.py   bioRxiv API -> data/preprints.json (60 in-lane, 30 deliberately off-lane); --server medrxiv
judge.py             the one prompt every model sees, and the parser that decides coverage
harness.py           preprints x models x 3 repeats through OpenRouter JSON mode -> data/results.jsonl
analyze.py           metrics table (results/results.md + .csv), bootstrap CIs, two figures, README sync
probes.py            bias probes: does the judge reward long abstracts? (len rho column, flagged vs the ceiling)
intern/              production run: fetch 14 days -> dedupe -> score once with hy3 -> email top 5 (launchd, biweekly)
gate.py              PASS/FAIL exit-code gate for the re-run (thresholds on results.csv + live model-id check)
agreement.py         chance-corrected agreement: kappa on the >= 0.5 decision, alpha over 0.1 bins, per-category verdicts
disagreement.py      the preprints the usable models split on most -> results/disagreement.md
baseline.py          zero-LLM control: tf-idf cosine(profile.md, title + abstract) as a derived row
ensembles.py         median-of-3 cheap models as derived rows (pre-registered combos only)
```

Metrics, per model config (definitions, and the analyses built on them, in
[docs/METRICS.md](docs/METRICS.md)):

| column             | one line                                                                          |
| ------------------ | --------------------------------------------------------------------------------- |
| **cov%** / ladder  | calls with a parseable score; strict / lenient / repaired parser rungs            |
| **wrong-field**    | off-lane calls scored >= 0.5                                                      |
| **sigma**          | spread across the 3 repeats                                                       |
| **MAE [95% CI]**   | distance from the ceiling, bootstrap interval over preprints                      |
| **P(<= best)**     | paired bootstrap: share of resamples where this row beats the best single model   |
| **rho / kappa / alpha / len rho** | rank, decision and binned agreement with the ceiling; length bias      |
| **top-10**         | how many of the ceiling's top ten the model also shortlisted                      |
| **latency, $/call** | measured, not the price sheet                                                    |

## Results

<!-- RESULTS:START -->

Run of 2026-09-11, re-scored 2026-09-12 after the `message.reasoning` fix, plus three
`json_schema` reruns on 2026-09-13: 90 preprints x 18 model configurations x 3 repeats =
4,860 calls, $2.82 measured, of which $1.06 was the ceiling and $0.63 the reruns.
Rows suffixed `#schema` ran with strict structured output instead of JSON mode; italic
rows are derived from other rows, not API calls.

| model | cov% | strict% | ladder strict / lenient / repaired | wrong-field | sigma | MAE vs ceiling [95% CI] | P(<= best) | rho | kappa | alpha | len rho | top-10 | latency s | $/call |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic/claude-sonnet-5 | 94.4 | 97.3 | 91.9 / 94.4 / 95.6 | 0 | 0.011 | 0.000 [0.000, 0.000] | 1.00 | 1.00 | 1.00 | 1.00 | 0.05 | 10/10 | 3.25 | 0.00394 |
| minimax/minimax-m3@low | 96.3 | 91.2 | 87.4 / 95.9 / 95.9 | 1 | 0.057 | 0.072 [0.054, 0.092] | 0.96 | 0.91 | 0.46 | 0.79 | 0.08 | 6/10 | 4.33 | 0.00027 |
| _ens:hy3+deepseek-v4-flash-0731@medium+mimo-v2.5_ | 100.0 | 100.0 | n/a / n/a / n/a | 0 | n/a | 0.085 [0.067, 0.105] | 0.66 | 0.91 | 0.46 | 0.73 | 0.07 | 6/10 | 14.66 | 0.00026 |
| tencent/hy3 | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 0 | 0.033 | 0.088 [0.068, 0.109] | 1.00 | 0.89 | 0.36 | 0.72 | 0.10 | 5/10 | 4.22 | 0.00006 |
| deepseek/deepseek-v4-flash-0731@medium | 99.6 | 100.0 | 99.6 / 99.6 / 99.6 | 1 | 0.047 | 0.092 [0.073, 0.112] | 0.35 | 0.90 | 0.54 | 0.70 | 0.05 | 6/10 | 13.89 | 0.00013 |
| _ens:hy3+mimo-v2.5+mercury-2.5_ | 100.0 | 100.0 | n/a / n/a / n/a | 0 | n/a | 0.093 [0.074, 0.113] | 0.20 | 0.91 | 0.36 | 0.68 | 0.07 | 7/10 | 6.78 | 0.00020 |
| deepseek/deepseek-v4-flash-0731@low | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 1 | 0.058 | 0.096 [0.077, 0.116] | 0.19 | 0.89 | 0.54 | 0.69 | 0.07 | 6/10 | 16.77 | 0.00014 |
| minimax/minimax-m3 | 97.0 | 100.0 | 97.0 / 97.0 / 97.0 | 1 | 0.054 | 0.099 [0.076, 0.123] | 0.16 | 0.92 | 0.38 | 0.69 | 0.07 | 8/10 | 2.46 | 0.00021 |
| xiaomi/mimo-v2.5 | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 2 | 0.065 | 0.103 [0.080, 0.125] | 0.06 | 0.88 | 0.43 | 0.66 | 0.09 | 6/10 | 5.55 | 0.00007 |
| _ens:hy3+gemini-3.5-flash-lite+deepseek-v4.1-flash_ | 100.0 | 100.0 | n/a / n/a / n/a | 0 | n/a | 0.106 [0.087, 0.127] | 0.00 | 0.91 | 0.46 | 0.71 | 0.10 | 9/10 | 6.00 | 0.00075 |
| qwen/qwen3.8-flash | 99.6 | 100.0 | 100.0 / 100.0 / 100.0 | 1 | 0.063 | 0.118 [0.090, 0.149] | 0.00 | 0.87 | 0.33 | 0.61 | 0.09 | 5/10 | 1.89 | 0.00010 |
| inception/mercury-2.5 | 99.3 | 99.6 | 98.9 / 99.3 / 100.0 | 0 | 0.062 | 0.120 [0.099, 0.143] | 0.00 | 0.90 | 0.33 | 0.59 | 0.08 | 6/10 | 0.89 | 0.00007 |
| inception/mercury-2.5#schema | 100.0 | 99.3 | 99.3 / 99.3 / 99.6 | 0 | 0.057 | 0.120 [0.100, 0.142] | 0.00 | 0.87 | 0.36 | 0.57 | 0.02 | 6/10 | 1.09 | 0.00007 |
| google/gemini-3.5-flash-lite | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 0 | 0.015 | 0.124 [0.096, 0.154] | 0.00 | 0.88 | 0.50 | 0.62 | 0.03 | 7/10 | 1.06 | 0.00044 |
| anthropic/claude-haiku-4.5 | 100.0 | 0.0 | 0.0 / 100.0 / 100.0 | 0 | 0.010 | 0.136 [0.117, 0.158] | 0.00 | 0.90 | 0.50 | 0.65 | 0.17 | 7/10 | 2.35 | 0.00161 |
| deepseek/deepseek-v4.1-flash | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 3 | 0.061 | 0.140 [0.116, 0.165] | 0.00 | 0.91 | 0.40 | 0.58 | 0.12 | 8/10 | 4.43 | 0.00025 |
| z-ai/glm-5.3-flash | 100.0 | 97.4 | 97.4 / 100.0 / 100.0 | 0 | 0.035 | 0.147 [0.124, 0.169] | 0.00 | 0.93 | 0.40 | 0.53 | 0.12 | 7/10 | 11.48 | 0.00050 |
| z-ai/glm-5.3-flash#schema | 100.0 | 99.6 | 99.6 / 100.0 / 100.0 | 1 | 0.033 | 0.153 [0.129, 0.177] | 0.00 | 0.93 | 0.35 | 0.51 | 0.09 | 7/10 | 9.91 | 0.00050 |
| anthropic/claude-haiku-4.5#schema | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 4 | 0.017 | 0.157 [0.133, 0.183] | 0.00 | 0.91 | 0.38 | 0.55 | 0.13 | 7/10 | 2.47 | 0.00176 |
| deepseek/deepseek-v4-flash-0731 | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 3 | 0.081 | 0.158 [0.135, 0.182] | 0.00 | 0.90 | 0.43 | 0.46 | 0.04 | 6/10 | 4.33 | 0.00008 |
| openai/gpt-5.6-luna | 100.0 | 100.0 | 100.0 / 100.0 / 100.0 | 2 | 0.024 | 0.181 [0.143, 0.222] | 0.00 | 0.93 | 0.25 | 0.43 | 0.17 | 5/10 | 1.80 | 0.00027 |
| _baseline:tfidf_ | 100.0 | 100.0 | n/a / n/a / n/a | 2 | n/a | n/a | n/a | 0.56 | n/a | n/a | 0.29 | 4/10 | 0.00 | 0.00000 |

Among configurations at >= 99% coverage, `tencent/hy3` has both the best agreement and the
lowest price, so it is the reference for the `P(<= best)` column. Read that column before
reading the ranking: the four rows below hy3 (DeepSeek V4 Flash at @medium and @low, MiniMax M3,
MiMo) all land between 0.06 and 0.35, so on 90 preprints hy3 leads them but does not separate
from them. From `qwen/qwen3.8-flash` down the gap is real (P = 0.00). `minimax/minimax-m3@low`
has the lowest MAE in the table and beats hy3 in 96% of resamples, but at 96.3% coverage it is
not usable as-is. `deepseek/deepseek-v4.1-flash` matched the most of the ceiling's own top ten
(8/10) while ranking near the bottom on MAE, which is why both columns are here. The two
MiniMax rows fall short on coverage for a plain reason: the model returns well-formed JSON
with no `fit_score` key in it, across four different providers.

Reproduce with `uv run python analyze.py` against `data/results.jsonl`.

<!-- RESULTS:END -->

![MAE against measured cost per call](results/fig_mae_vs_cost.png)
![Coverage by model configuration](results/fig_coverage.png)

## More analyses

Baselines, ensembles, chance-corrected agreement by category, bias probes and the
disagreement audit are in [docs/METRICS.md](docs/METRICS.md); their outputs live in
[`results/`](results/).

## Run it

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

## The intern, in production

`python -m intern` is the thing this repo was built to choose a model for: every other Thursday
it pulls the last two weeks of in-lane bioRxiv preprints, drops the DOIs it has already sent,
scores each once with the gate-approved model (`tencent/hy3`, reasoning off, about half a cent
per run), and emails the top five to your own inbox over Gmail SMTP. It runs locally under
launchd, so the Gmail app password never leaves the machine; it refuses to send if the last
digest went out under 13 days ago (launchd has no biweekly trigger), and aborts if a run would
cost more than $0.10.

```bash
uv run python -m intern --dry-run              # render the digest to stdout; sends nothing
mkdir -p ~/.preprint-judge
cp credentials.json.example ~/.preprint-judge/credentials.json   # then fill in the Gmail fields
chmod 600 ~/.preprint-judge/credentials.json
./scripts/install-launchd.sh                   # Thursday 14:00 weekly; biweekly enforced in code
```

See [SECURITY.md](SECURITY.md) for what it reads and sends.

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

## Method notes

Moved to [docs/METRICS.md](docs/METRICS.md#method-notes): same prompt for every model, reasoning
switches, timeouts, measured cost, provider routing, the parser ladder, structured output.

## Caveats

You are calibrating to a model, not to truth. A cheap judge with MAE 0.05 against the
ceiling inherits every blind spot the ceiling has. The ceiling's own wrong-field count
is the only check on that in this repo, and it is a weak one. Read the post for the
longer version.

## Security

See [SECURITY.md](SECURITY.md) for what the code reads, sends, and never commits.

## License

MIT.
