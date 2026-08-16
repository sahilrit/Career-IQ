"""Minimal transactional email, stdlib only (smtplib) — no paid service.

Configured entirely by environment: if SMTP is set, ``send_email`` sends;
otherwise it returns False so the caller can fall back (e.g. show a
password-reset link on screen for a self-serve / single-node install).

Env: CAREEROS_SMTP_HOST, CAREEROS_SMTP_PORT (default 587),
CAREEROS_SMTP_USER, CAREEROS_SMTP_PASSWORD, CAREEROS_EMAIL_FROM.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(os.environ.get("CAREEROS_SMTP_HOST") and os.environ.get("CAREEROS_EMAIL_FROM"))


def send_email(*, to: str, subject: str, body: str) -> bool:
    """Send a plain-text email. Returns True on success, False if SMTP
    isn't configured or the send fails (the caller should degrade)."""
    if not smtp_configured():
        return False
    message = EmailMessage()
    message["From"] = os.environ["CAREEROS_EMAIL_FROM"]
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    host = os.environ["CAREEROS_SMTP_HOST"]
    port = int(os.environ.get("CAREEROS_SMTP_PORT", "587"))
    user = os.environ.get("CAREEROS_SMTP_USER")
    password = os.environ.get("CAREEROS_SMTP_PASSWORD")
    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
        return True
    except (smtplib.SMTPException, OSError):
        return False
