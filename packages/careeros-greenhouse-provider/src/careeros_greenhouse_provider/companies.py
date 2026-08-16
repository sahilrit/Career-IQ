"""Seed list of company Greenhouse boards (public board tokens).

Every token here was verified live to return jobs. Over-inclusion is
still safe: the transport skips any board that later 404s or errors, so
a stale token just drops out silently. Pass your own tuple to
``GreenhouseProvider`` / ``HttpxGreenhouseTransport`` to narrow or extend.
"""

from __future__ import annotations

DEFAULT_COMPANY_BOARDS: tuple[str, ...] = (
    "affirm",
    "airbnb",
    "airtable",
    "betterment",
    "bitpanda",
    "blend",
    "brave",
    "brex",
    "cameo",
    "carta",
    "checkr",
    "chime",
    "cloudflare",
    "coinbase",
    "collectivehealth",
    "coreweave",
    "databricks",
    "datadog",
    "discord",
    "dropbox",
    "duolingo",
    "elastic",
    "faire",
    "figma",
    "flexport",
    "gemini",
    "gitlab",
    "gusto",
    "instacart",
    "lyft",
    "marqeta",
    "mercury",
    "mongodb",
    "pinterest",
    "postman",
    "reddit",
    "ripple",
    "robinhood",
    "roblox",
    "samsara",
    "scaleai",
    "sofi",
    "stripe",
    "twitch",
    "upstart",
    "webflow",
)
