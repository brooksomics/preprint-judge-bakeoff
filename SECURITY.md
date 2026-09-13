# Security

## What this repo reads

- `OPENROUTER_API_KEY`, from the environment only (`.env` is gitignored; `.env.example`
  is the template).
- Optionally `~/.preprint-judge/credentials.json` (mode 600) for the digest mailer:
  a Gmail address and an app password. Nothing under `~/.preprint-judge/` is tracked.

## What it sends, and where

- To OpenRouter: your `profile.md`, plus each preprint's title and abstract, inside one
  chat completion per call. OpenRouter routes to the provider listed in the row.
- To your own inbox, over Gmail SMTP with TLS (port 465): the digest of top-scored
  preprints. Nothing else leaves the machine.

## What is never committed

`.env`, `credentials.json`, `seen.json`, `*.log` other than the published `data/run.log`.
A `forbid-local-state` pre-commit hook rejects them if staged, `gitleaks` runs on every
commit and over full history in CI, and `scripts/firewall_scan.py` blocks absolute home
paths, personal email addresses, and key-shaped assignments. Locally it also applies a
private denylist kept outside the repo; the terms are not published, only the scanner.

## Rotating credentials

- OpenRouter: create a new key at `https://openrouter.ai/settings/keys`, put it in `.env`,
  delete the old key there. Cost caps live on the key, so set one.
- Gmail app password: Google Account -> Security -> 2-Step Verification -> App passwords.
  Revoke the old one, write the new one into `~/.preprint-judge/credentials.json`.

## The intern (`python -m intern`)

- **Reads:** `OPENROUTER_API_KEY` from the environment (launchd passes `.env` via `uv run
  --env-file`), and `~/.preprint-judge/credentials.json` (mode 600: Gmail sender, app password,
  receiver). State in `~/.preprint-judge/seen.json` and `intern.log`. None of it is in the repo;
  `.gitignore` and the `forbid-local-state` hook both refuse those filenames.
- **Sends:** each preprint's title and abstract plus `profile.md` to OpenRouter (one call per
  preprint, hard budget $0.10 per run), and one digest email to *your own* inbox over Gmail
  SMTP_SSL on port 465. Nothing else leaves the machine. `--dry-run` sends nothing.
- **Rotate the app password:** revoke it at https://myaccount.google.com/apppasswords, create a
  new one, write it into `~/.preprint-judge/credentials.json`.

## Reporting

Open an issue, or email the address on the author's GitHub profile if it is sensitive.
