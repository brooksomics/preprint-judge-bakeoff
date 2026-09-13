"""Render and send the digest over Gmail SMTP_SSL (port 465), HTML plus a plain-text part."""

from __future__ import annotations

import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import NamedTuple

from intern.credentials import Gmail

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 465
BIORXIV = "https://www.biorxiv.org/content/{doi}v{version}"


class Digest(NamedTuple):
    picks: list[dict]
    cost_usd: float
    run_date: date


def subject(d: Digest) -> str:
    return f"Preprint intern: {len(d.picks)} picks for {d.run_date.isoformat()}"


def _url(p: dict) -> str:
    return BIORXIV.format(doi=p["doi"], version=p.get("version") or "1")


def html_body(d: Digest) -> str:
    items = [
        f'<li><a href="{_url(p)}">{escape(p["title"])}</a> '
        f"<b>{p['fit_score']:.2f}</b> &middot; {escape(p.get('field') or '')}<br>"
        f"<small>{escape(p.get('rationale') or '')} (${p.get('cost_usd') or 0:.5f})</small></li>"
        for p in d.picks
    ]
    return (
        f"<h2>{escape(subject(d))}</h2><ol>{''.join(items)}</ol>"
        f"<p><small>Scored the last two weeks of in-lane bioRxiv preprints. "
        f"Run cost ${d.cost_usd:.4f} (OpenRouter usage.cost).</small></p>"
    )


def text_body(d: Digest) -> str:
    lines = [subject(d), ""]
    for i, p in enumerate(d.picks, 1):
        lines.append(f"{i}. {p['title']}  [{p['fit_score']:.2f}] {p.get('field') or ''}")
        lines.append(f"   {_url(p)}")
        lines.append(f"   {p.get('rationale') or ''}")
    lines += ["", f"Run cost ${d.cost_usd:.4f} (OpenRouter usage.cost)."]
    return "\n".join(lines)


def build(creds: Gmail, d: Digest) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = subject(d), creds.sender, creds.receiver
    msg.attach(MIMEText(text_body(d), "plain"))
    msg.attach(MIMEText(html_body(d), "html"))
    return msg


def send(creds: Gmail, d: Digest) -> None:
    """One digest to your own inbox. Raises smtplib errors on failure."""
    msg = build(creds, d)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(creds.sender, creds.app_password)
        server.sendmail(creds.sender, creds.receiver, msg.as_string())
