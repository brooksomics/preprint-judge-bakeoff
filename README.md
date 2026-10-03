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

Short answer: `minimax/minimax-m3@low` agrees best with the ceiling (MAE 0.072), and
`tencent/hy3` is the cheapest close second (MAE 0.088 at $0.00006 a call, 4.5 times less), which
is why the intern runs it. The full table, and how to read it, is in
[docs/RESULTS.md](docs/RESULTS.md).

![MAE against measured cost per call](results/fig_mae_vs_cost.png)

## What's here

```
fetch_preprints.py   bioRxiv API -> data/preprints.json (60 in-lane, 30 deliberately off-lane); --server medrxiv
judge.py             the one prompt every model sees, and the parser that decides coverage
harness.py           preprints x models x 3 repeats through OpenRouter JSON mode -> data/results.jsonl
analyze.py           metrics table (results/results.md + .csv), bootstrap CIs, two figures, docs/RESULTS.md sync
probes.py            bias probes: does the judge reward long abstracts? (len rho column, flagged vs the ceiling)
intern/              production run: 14 days of bioRxiv/medRxiv/arXiv -> hy3 -> break ties -> email top 5
gate.py              PASS/FAIL exit-code gate for the re-run (thresholds on results.csv + live model-id check)
agreement.py         chance-corrected agreement: kappa on the >= 0.5 decision, alpha over 0.1 bins, per-category verdicts
disagreement.py      the preprints the usable models split on most -> results/disagreement.md
baseline.py          zero-LLM control: tf-idf cosine(profile.md, title + abstract) as a derived row
ensembles.py         median-of-3 cheap models as derived rows (pre-registered combos only)
```

## Quick start

```bash
uv sync
export OPENROUTER_API_KEY=...              # or put it in .env and `set -a; source .env`
uv run python harness.py --smoke           # 2 preprints x 1 repeat per model: every id resolves
uv run python -m intern --dry-run          # today's digest to stdout; sends nothing
```

## Docs

- [docs/RESULTS.md](docs/RESULTS.md): the full table, the figures, and how to read them
- [docs/METRICS.md](docs/METRICS.md): what every column means; baselines, ensembles,
  agreement by category, bias probes, the disagreement audit, method notes
- [docs/RUNNING.md](docs/RUNNING.md): the full run, re-running with the gate, and pointing it at
  your own profile
- [docs/INTERN.md](docs/INTERN.md): the production intern: fetch, scoring, tie-breaks, install
- [SECURITY.md](SECURITY.md): what the code reads, sends, and never commits

## Caveats

You are calibrating to a model, not to truth. A cheap judge with MAE 0.05 against the
ceiling inherits every blind spot the ceiling has. The ceiling's own wrong-field count
is the only check on that in this repo, and it is a weak one. Read the post for the
longer version.

## License

MIT.
