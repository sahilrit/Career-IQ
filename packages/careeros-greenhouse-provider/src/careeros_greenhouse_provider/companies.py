"""Seed list of company Greenhouse boards.

These are verified public boards (each hires across functions, remote
included). The list is a default, not a limit — pass your own to
``GreenhouseProvider`` / ``HttpxGreenhouseTransport``. Every one links to
an open Greenhouse-hosted application form.
"""

from __future__ import annotations

DEFAULT_COMPANY_BOARDS: tuple[str, ...] = (
    "stripe",
    "databricks",
    "mongodb",
    "cloudflare",
    "brex",
    "elastic",
    "pinterest",
    "lyft",
    "coinbase",
    "figma",
    "reddit",
    "robinhood",
    "instacart",
    "gitlab",
    "gusto",
    "faire",
    "discord",
    "twitch",
    "dropbox",
    "airtable",
    "brave",
)
