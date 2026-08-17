"""Lightweight storefront audit: fetch the prospect's homepage over HTTP and
flag missing conversion signals from the HTML. No browser required (works on
the free tier), so the Pitch Kit can audit the *real* site, not just its ads.

It only reads the public homepage the prospect already serves to everyone —
no login, no scraping behind auth — and degrades to an empty list on any
error, so a pitch is never blocked by a site that won't load."""

from __future__ import annotations

import httpx

from careeros_audit_proposal_engine import Finding

_UA = "Mozilla/5.0 (compatible; CareerOS-Audit/1.0; +https://careeros.app)"

# Each check: (category, keywords that indicate the signal is PRESENT,
# detail when missing, recommendation when missing).
_CHECKS: list[tuple[str, tuple[str, ...], str, str]] = [
    (
        "trust",
        ("review", "trustpilot", "judge.me", "loox", "yotpo", "stars", "rated"),
        "No visible customer reviews or social proof on the homepage.",
        "Add a reviews widget and star ratings near the hero and product cards.",
    ),
    (
        "trust",
        ("secure checkout", "money-back", "guarantee", "ssl", "satisfaction"),
        "No trust badges or guarantees found.",
        "Add a money-back guarantee and secure-checkout badges to reduce hesitation.",
    ),
    (
        "offer",
        ("free shipping", "free delivery"),
        "No free-shipping offer surfaced.",
        "Add a free-shipping threshold bar at the top of the site.",
    ),
    (
        "urgency",
        ("only", "limited", "hurry", "selling fast", "ends", "countdown", "low stock"),
        "No urgency or scarcity cues detected.",
        "Add tasteful urgency (limited stock / offer countdown) on product pages.",
    ),
    (
        "checkout",
        ("shop pay", "apple pay", "google pay", "paypal", "express checkout"),
        "No express-checkout options detected.",
        "Enable Shop Pay / Apple Pay / PayPal express checkout to cut friction.",
    ),
    (
        "mobile",
        ('name="viewport"', "width=device-width"),
        "No responsive viewport meta tag found.",
        "Add a responsive viewport meta tag so the store renders well on mobile.",
    ),
]


def _normalize(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def audit_storefront(website: str, *, http_client: httpx.Client | None = None) -> list[Finding]:
    url = _normalize(website)
    if not url:
        return []
    client = http_client or httpx.Client(timeout=10.0, follow_redirects=True)
    try:
        response = client.get(url, headers={"User-Agent": _UA})
    except httpx.HTTPError:
        return []
    finally:
        if http_client is None:
            client.close()
    if response.status_code >= 400:
        return []

    html = response.text.lower()
    findings: list[Finding] = []
    for category, keywords, detail, recommendation in _CHECKS:
        if not any(keyword in html for keyword in keywords):
            findings.append(
                Finding(category=category, detail=detail, recommendation=recommendation)
            )
    return findings
