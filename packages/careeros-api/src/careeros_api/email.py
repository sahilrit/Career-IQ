"""Minimal transactional email over stdlib SMTP — no paid service. Sends
only when SMTP is configured; otherwise callers degrade gracefully."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def smtp_configured() -> bool:
    return bool(os.environ.get("CAREEROS_SMTP_HOST") and os.environ.get("CAREEROS_EMAIL_FROM"))


def app_base_url() -> str:
    return os.environ.get("CAREEROS_APP_BASE_URL", "http://localhost:3000").rstrip("/")


def send_email(*, to: str, subject: str, body: str) -> bool:
    """Send a plaintext email. Returns False if unconfigured or on failure."""
    if not smtp_configured():
        return False
    host = os.environ["CAREEROS_SMTP_HOST"]
    port = int(os.environ.get("CAREEROS_SMTP_PORT", "587"))
    user = os.environ.get("CAREEROS_SMTP_USER")
    password = os.environ.get("CAREEROS_SMTP_PASSWORD")
    sender = os.environ["CAREEROS_EMAIL_FROM"]

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
        return True
    except (smtplib.SMTPException, OSError):
        return False
