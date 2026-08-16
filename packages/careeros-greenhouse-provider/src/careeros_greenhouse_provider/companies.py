"""Seed list of company Greenhouse boards.

These are public board tokens for companies known to use Greenhouse and
hire remote roles across functions (marketing, growth, ops, sales,
engineering). Over-inclusion is safe: the transport skips any board that
404s or errors, so a stale token just drops out silently. Pass your own
tuple to ``GreenhouseProvider`` / ``HttpxGreenhouseTransport`` to narrow
or extend it.
"""

from __future__ import annotations

DEFAULT_COMPANY_BOARDS: tuple[str, ...] = (
    # fintech / payments
    "stripe",
    "brex",
    "mercury",
    "affirm",
    "marqeta",
    "upstart",
    "sofi",
    "wealthfront",
    "betterment",
    "carta",
    "chime",
    "plaid",
    "coinbase",
    "robinhood",
    "nerdwallet",
    # data / infra / dev tools
    "databricks",
    "mongodb",
    "datadog",
    "cloudflare",
    "elastic",
    "confluent",
    "hashicorp",
    "snowflakecomputing",
    "sourcegraph",
    "retool",
    "webflow",
    "gitlab",
    "grammarly",
    # marketplaces / consumer / commerce
    "faire",
    "instacart",
    "lyft",
    "doordash",
    "pinterest",
    "reddit",
    "discord",
    "twitch",
    "dropbox",
    "airtable",
    "roblox",
    "thumbtack",
    "whatnot",
    "cameo",
    "flexport",
    "samsara",
    # ops / hr / trust
    "gusto",
    "checkr",
    "lattice",
    "gong",
    "brave",
    "figma",
)
