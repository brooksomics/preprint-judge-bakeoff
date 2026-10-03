# The intern, in production

`python -m intern` is the thing this repo was built to choose a model for: every other Thursday
it pulls every preprint first posted in the last two weeks to the in-lane categories of bioRxiv,
medRxiv (`MED_IN_LANE`) and arXiv q-bio (GN, QM, BM, PE), about 950 papers, drops the DOIs it
has already sent, scores each once (retrying a call that returns no score, up to twice) with
the gate-approved model (`tencent/hy3`, reasoning off, seven to ten cents per run, measured),
and emails the top five to your own inbox over Gmail SMTP. The bioRxiv API is oldest-first with
no sort option, so it pages the whole window rather
than capping it: a cap would drop the newest days, and since windows abut, drop them for good.
Hy3 scores coarsely (74 of 948 papers tied at 0.85 on 2026-10-02), so the group tied at the
top-five cutoff is re-scored once by DeepSeek V4.1 Flash, about two cents; on that window it
lifted the mean ceiling score of the five picks from 0.69 (random tie-break) to 0.84, against
0.88 for the ceiling itself. Whatever DeepSeek leaves tied goes, in order, to a corresponding
author at an OpenAlex top-200 institution, then an abstract that names code or a public dataset,
then, only if you configure it, similarity to your own past picks ([`intern/tiebreak.py`](../intern/tiebreak.py) has the
evidence for each key). It runs locally under launchd, so its credentials never leave the
machine (both secrets in that one mode-600 file, because launchd starts no shell to source
`.env` from); it refuses to send if the last digest went out under 13 days ago (launchd has no
biweekly trigger), and aborts if a run would cost more than $0.25.

The similarity key is off by default, because its reference text is one reader's history. To turn
it on, add to the credentials file a URL serving your write-ups in `llms-full.txt` form (each
post a `### Title` line then a `URL:` line) and the title prefix that marks a pick:
`"past_picks": {"url": "https://example.org/llms-full.txt", "title_prefix": "Journal Safari"}`.

```bash
uv run python -m intern --dry-run              # render the digest to stdout; sends nothing
mkdir -p ~/.preprint-judge
cp credentials.json.example ~/.preprint-judge/credentials.json   # Gmail fields + your OpenRouter key
chmod 600 ~/.preprint-judge/credentials.json
./scripts/install-launchd.sh                   # Thursday 14:00 weekly; biweekly enforced in code
```

See [SECURITY.md](../SECURITY.md) for what it reads and sends.
