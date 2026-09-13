# Metrics and analyses

Every column in `results/results.csv`, how it is computed, and the analyses that hang off it.
All numbers are computed from `data/results.jsonl` by `analyze.py`; nothing here is typed in.

## Columns

| metric             | meaning                                                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **cov%**           | calls that returned a parseable 0-1 score. Timeouts, bad JSON, and empty content count against it.                               |
| **ladder**         | the parser ladder: % of all calls parseable as clean JSON (strict), as the first JSON object in the body (lenient, the headline cov%), and after `json_repair` fixes a trailing comma, control character or missing quote (repaired). The score is never repaired: no numeric `fit_score` in [0, 1] means uncovered on every rung. |
| **strict%**        | of the covered calls, the share whose whole body was one clean JSON object (nothing before or after it). |
| **wrong-field**    | calls on an off-lane preprint scored >= 0.5. Counts calls, not preprints: one preprint misjudged on all 3 repeats contributes 3. |
| **sigma**          | mean per-preprint std dev across the 3 repeats. Repeatability.                                                                   |
| **MAE vs ceiling** | mean over preprints of \|model mean - ceiling mean\|. Agreement with the frontier model. The bracket is a 95% bootstrap interval: the 90 preprints resampled with replacement 2,000 times (seed 0), percentile method. |
| **P(<= best)**     | paired bootstrap against the best usable model (lowest MAE at >= 99% coverage): the share of those same 2,000 resamples in which this model's MAE is at or below the reference's. 1.00 for the reference itself; near 0 means the gap is real, near 0.5 means the two are not separable on 90 preprints. |
| **rho**            | Spearman rank correlation between the model's and the ceiling's per-preprint mean scores. Scale-free, so it is the column on which derived rows (`baseline:`) are comparable. |
| **kappa**          | Cohen's kappa between the model's and the ceiling's *decision* on each preprint (score >= 0.5), chance-corrected. 1.0 for the ceiling itself. |
| **alpha**          | Krippendorff's alpha, two raters, scores binned to 0.1 with squared-bin-difference distance (what the cited implementation calls ordinal). n/a for the unscaled baseline. |
| **len rho**        | Spearman between abstract word count and the model's mean score. Read it against the ceiling's own value: the analyzer flags models more than 0.2 away from it. |
| **top-10**         | of the ceiling's 10 highest-scoring preprints, how many are in the model's own top 10. Not bootstrapped: resampling preprints changes what "top 10" means, so this is a point count only. |
| **latency**        | mean wall-clock seconds per call.                                                                                                |
| **$/call**         | mean cost per call as reported by OpenRouter, not the price sheet. Summed for ensembles. |
| **derived**        | CSV only: True for rows computed from other rows (`baseline:`, `ens:`). Never the paired-test reference. |
| **kappa_top10**    | CSV only: Cohen's kappa on top-10 membership, the shortlist decision itself. |
| **n_calls**        | CSV only: rows behind the label (270 for a full 90 x 3 run). |                                                               |

## Baselines

Every model in the table has to beat a free method. `baseline:tfidf` scores each preprint by
the cosine between a tf-idf vector of `profile.md` and one of its title + abstract (stdlib
only: tf = 1 + log(count), idf = log((N + 1) / (df + 1)) over the 90 preprints, then min-max to
[0, 1]). It costs nothing, always answers, and its row sits in the table like any other. Its
scale is not a fit score, so its MAE against the ceiling is marked n/a; compare it on **rho**
(Spearman rank correlation with the ceiling's per-preprint means, reported for every row) and
on **top-10**. A model whose rho or top-10 does not clear the baseline is not adding anything
tf-idf would not have. Not tried: sentence-embedding cosine, which would need a dependency this
repo does not have; the "corpus" variant (cosine to the abstracts of past picks instead of the
profile) is the obvious next control.

## Ensembles

Compound judges are the thesis of frameworks like [Verdict](https://github.com/haizelabs/verdict):
instead of one call, aggregate several. The `ens:` rows are the cheapest version of that idea,
computed from scores already in `data/results.jsonl`: per preprint, the **median** of three
models' mean scores. Cost is the three costs summed, latency the slowest of the three, and the
row is unscored wherever any component failed, so its coverage is all-or-nothing. They are
italic in the table and carry `derived = True` in the CSV; the `P(<= best)` reference is
always a single model.

Three combinations are reported, chosen by rule before any ensemble was scored: the best-MAE,
steadiest-sigma and best-top-10 usable models together; the three cheapest usable models; and
the three lowest-MAE usable models from three different labs. There was deliberately no search
over combinations. Picking the best of many ensembles on the same 90 preprints the table is
scored on would be optimistic by construction, and even these three are post-hoc in the sense
that the components were chosen from this table.

## Chance-corrected agreement, by category

MAE rewards a judge that says "no" to almost everything, because the ceiling does too. The
`kappa` and `alpha` columns correct for that chance agreement, and
[`results/agreement_by_category.md`](../results/agreement_by_category.md) breaks kappa down by
bioRxiv category (the four in-lane categories, with the off-lane papers pooled) so a judge that
is reliable on genomics and unreliable on microbiology does not hide behind one number. The
verdict rule follows [judgecal](https://github.com/bengodgart/llm-judge-calibration): a
category is **reliable** when kappa >= 0.60 and it holds at least 8 preprints, else not. The
CSV also carries `kappa_top10`, the same statistic on top-10 membership.

## Bias probes

What was tested: **length.** For every row, `len rho` is the Spearman correlation between an
abstract's word count and the model's mean score for it. The ceiling has its own value, so the
question is not "is rho zero" but "does the cheap judge reward length more or less than the
model it is calibrated to"; `analyze.py` prints the rows more than 0.2 away from the ceiling.

What was not tested, and why: **position bias** (one abstract per call, nothing to reorder),
**self-preference** (no model here judges its own writing), and the **padded-twin verbosity
probe** used by pairwise judges (this judge never sees two candidates side by side, so padding
one of them has no analogue). If the judge ever moves to pairwise ranking, those three are the
first probes to add.

## Where the models disagree

MAE says how far a model sits from the ceiling on average. It says nothing about *which*
papers it gets wrong, and those are the ones worth a human's time. [`results/disagreement.md`](../results/disagreement.md)
ranks the 90 preprints by the population std dev of the usable models' mean scores (the
same >= 99% coverage set as the table, ceiling excluded), names the model at each extreme
next to the ceiling's own score, and lists the mirror image: the preprints every model
agrees on. Regenerate with `uv run python analyze.py --top-disagreement 10`.

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
- **Structured output fixes the fence and nothing else.** Three models were rerun with
  `response_format: {"type": "json_schema", "strict": true}` and the score schema from
  `judge.SCHEMA` (rows suffixed `#schema`). Haiku 4.5 goes from 0.0% strict JSON to
  100.0%: the markdown fence is gone. Its agreement does not improve, it worsens, MAE
  0.136 [0.117, 0.158] to 0.157 [0.133, 0.183], and it
  scores 4 off-lane calls at 0.5 or above where JSON mode scored 0. GLM 5.3 Flash
  (0.147 to 0.153) and Mercury 2.5 (0.120 to 0.120) sit inside their own intervals;
  Mercury's coverage moves from 99.3 to 100.0. Cost per call is unchanged for all three.
  Structured output is a parser guarantee, not a judgment upgrade; if your parser already takes
  the first JSON object, it buys you the `strict%` column and nothing in the columns that matter.
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
- **Read the answer out of whichever field it arrives in.** One provider (Parasail, serving
  minimax/minimax-m3) returns the completion in `message.reasoning` and leaves `message.content`
  null, with or without a `reasoning` parameter in the request. Reading only `content` booked 77
  complete answers in this run as coverage failures and scored that model at 79.6% instead of
  97.0%. `harness.unpack` now falls back to `reasoning` and records `content_field`.
- **A parseable score is not clean JSON, so the parser is a ladder.** Claude Haiku 4.5 wrapped
  all 270 of its JSON-mode responses in a ` ```json ` markdown fence, so a bare `json.loads()`
  scores it at 0% coverage. `judge.parse` tries strict `json.loads`, then the first JSON object
  in the body, then [`json_repair`](https://github.com/mangiucugna/json_repair), and records
  which rung answered as `parse_tier`. The headline `cov%` is the lenient rung, so the numbers
  the write-up quotes do not move; the `ladder` column shows all three. In this run the repair
  rung recovers the ceiling's own three parse failures (two control characters, one trailing
  comma) and two Mercury 2.5 bodies; everything else that failed was well-formed JSON with no
  `fit_score` key, which no repair can supply. The harness stores at most 2,000 characters of
  each body, so a few long responses cannot be re-parsed post hoc; `analyze.py` prints how many.
- The ceiling is scored with the same 3 repeats, so its row shows its own sigma and
  how many "wrong-field" calls the ceiling itself makes.
