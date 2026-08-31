"""Which company boards CareerOS crawls, per ATS.

Hosted ATSes have no global search API — Greenhouse cannot tell you "every
Greenhouse job matching 'growth marketer'". Discovery is therefore
company-scoped: you crawl boards you have named. That is the single most
important structural fact about ATS discovery, and it is why this file exists
rather than a clever search abstraction.

Every slug here was verified live against its board API (see
``scripts/verify_ats_boards.py``); ones that did not answer were removed
rather than left in hopefully. A slug that dies later is skipped at crawl time
and reported, so this list degrades quietly rather than breaking a search.
"""

from __future__ import annotations

import json
import os
import re

from careeros_ats_providers.adapter import BoardEntry


def _entries(pairs: tuple[tuple[str, str], ...]) -> list[BoardEntry]:
    return [BoardEntry(slug, name) for slug, name in pairs]


GREENHOUSE_BOARDS: tuple[tuple[str, str], ...] = (
    ("stripe", "Stripe"),
    ("airbnb", "Airbnb"),
    ("databricks", "Databricks"),
    ("cloudflare", "Cloudflare"),
    ("coinbase", "Coinbase"),
    ("dropbox", "Dropbox"),
    ("robinhood", "Robinhood"),
    ("reddit", "Reddit"),
    ("discord", "Discord"),
    ("figma", "Figma"),
    ("gitlab", "GitLab"),
    ("mongodb", "MongoDB"),
    ("twilio", "Twilio"),
    ("instacart", "Instacart"),
    ("pinterest", "Pinterest"),
    ("lyft", "Lyft"),
    ("brex", "Brex"),
    ("carta", "Carta"),
    ("mercury", "Mercury"),
    ("vercel", "Vercel"),
    ("webflow", "Webflow"),
    ("duolingo", "Duolingo"),
    ("asana", "Asana"),
    ("elastic", "Elastic"),
    ("datadog", "Datadog"),
    ("samsara", "Samsara"),
    ("affirm", "Affirm"),
    ("chime", "Chime"),
    ("gusto", "Gusto"),
    ("klaviyo", "Klaviyo"),
    ("lattice", "Lattice"),
    ("wise", "Wise"),
    ("monzo", "Monzo"),
    ("intercom", "Intercom"),
    ("postman", "Postman"),
    ("netlify", "Netlify"),
    ("mixpanel", "Mixpanel"),
    ("faire", "Faire"),
    ("flexport", "Flexport"),
    ("checkr", "Checkr"),
    ("marqeta", "Marqeta"),
    ("sofi", "SoFi"),
    ("upstart", "Upstart"),
    ("nextdoor", "Nextdoor"),
    ("okta", "Okta"),
    ("roblox", "Roblox"),
    ("twitch", "Twitch"),
    ("zocdoc", "Zocdoc"),
    ("calendly", "Calendly"),
    ("launchdarkly", "LaunchDarkly"),
    ("fivetran", "Fivetran"),
    ("coreweave", "CoreWeave"),
    ("scaleai", "Scale AI"),
    ("sigmacomputing", "Sigma Computing"),
    ("betterment", "Betterment"),
    ("pendo", "Pendo"),
    ("life360", "Life360"),
    ("airtable", "Airtable"),
    ("brave", "Brave"),
    ("udemy", "Udemy"),
    ("zoominfo", "ZoomInfo"),
    ("blend", "Blend"),
    ("cameo", "Cameo"),
    ("bitpanda", "Bitpanda"),
    ("ripple", "Ripple"),
    ("gemini", "Gemini"),
    ("instabase", "Instabase"),
    ("collectivehealth", "Collective Health"),
    ("rockstargames", "Rockstar Games"),
    ("peloton", "Peloton"),
)

LEVER_BOARDS: tuple[tuple[str, str], ...] = (
    ("gopuff", "Gopuff"),
    ("veeva", "Veeva"),
    ("palantir", "Palantir"),
    ("spotify", "Spotify"),
    ("matchgroup", "Match Group"),
    ("mistral", "Mistral AI"),
)

ASHBY_BOARDS: tuple[tuple[str, str], ...] = (
    ("openai", "OpenAI"),
    ("harvey", "Harvey"),
    ("elevenlabs", "ElevenLabs"),
    ("sierra", "Sierra"),
    ("ramp", "Ramp"),
    ("notion", "Notion"),
    ("cursor", "Cursor"),
    ("vanta", "Vanta"),
    ("perplexity", "Perplexity"),
    ("mercor", "Mercor"),
    ("replit", "Replit"),
    ("clickup", "ClickUp"),
    ("supabase", "Supabase"),
    ("linear", "Linear"),
    ("posthog", "PostHog"),
    ("zapier", "Zapier"),
    ("deel", "Deel"),
)

SMARTRECRUITERS_BOARDS: tuple[tuple[str, str], ...] = (
    ("BoschGroup", "Bosch"),
    ("AveryDennison", "Avery Dennison"),
    ("Ubisoft2", "Ubisoft"),
    ("McDonaldsCorporation", "McDonald's"),
)

WORKABLE_BOARDS: tuple[tuple[str, str], ...] = (
    ("spotawheel", "Spotawheel"),
    ("blueground", "Blueground"),
    ("sunlight", "Sunlight"),
    ("upstream", "Upstream"),
    ("orfium", "Orfium"),
    ("epignosis", "Epignosis"),
    ("skroutz", "Skroutz"),
    ("persado", "Persado"),
)

RECRUITEE_BOARDS: tuple[tuple[str, str], ...] = (
    ("channable", "Channable"),
    ("nmbrs", "Nmbrs"),
    ("dashmote", "Dashmote"),
)

PERSONIO_BOARDS: tuple[tuple[str, str], ...] = (
    ("urbansportsclub", "Urban Sports Club"),
    ("penta", "Penta"),
)

BAMBOOHR_BOARDS: tuple[tuple[str, str], ...] = (
    ("canopy", "Canopy"),
    ("gitkraken", "GitKraken"),
)

#: Workday boards need tenant + regional host + site name, which cannot be
#: derived from a company name — each is added deliberately. All verified live.
WORKDAY_BOARDS: tuple[dict, ...] = (
    {"slug": "nvidia", "name": "NVIDIA", "region": "wd5", "site": "NVIDIAExternalCareerSite"},
    {"slug": "salesforce", "name": "Salesforce", "region": "wd12", "site": "External_Career_Site"},
    {"slug": "cisco", "name": "Cisco", "region": "wd5", "site": "Cisco_Careers"},
    {"slug": "hpe", "name": "HPE", "region": "wd5", "site": "Jobsathpe"},
    {"slug": "mastercard", "name": "Mastercard", "region": "wd1", "site": "CorporateCareers"},
    {"slug": "adobe", "name": "Adobe", "region": "wd5", "site": "external_experienced"},
    {"slug": "workday", "name": "Workday", "region": "wd5", "site": "Workday"},
    {"slug": "paypal", "name": "PayPal", "region": "wd1", "site": "jobs"},
)


def greenhouse_boards() -> list[BoardEntry]:
    return _entries(GREENHOUSE_BOARDS)


def lever_boards() -> list[BoardEntry]:
    return _entries(LEVER_BOARDS)


def ashby_boards() -> list[BoardEntry]:
    return _entries(ASHBY_BOARDS)


def smartrecruiters_boards() -> list[BoardEntry]:
    return _entries(SMARTRECRUITERS_BOARDS)


def workable_boards() -> list[BoardEntry]:
    return _entries(WORKABLE_BOARDS)


def recruitee_boards() -> list[BoardEntry]:
    return _entries(RECRUITEE_BOARDS)


def personio_boards() -> list[BoardEntry]:
    return _entries(PERSONIO_BOARDS)


def bamboohr_boards() -> list[BoardEntry]:
    return _entries(BAMBOOHR_BOARDS)


#: Every field a Workday tenant needs. Validated up front, because a tenant
#: with a missing ``site`` fails at crawl time with a 404 that reads like the
#: company deleted its board.
WORKDAY_REQUIRED_KEYS = ("slug", "region", "site")


class WorkdayConfigError(ValueError):
    """A Workday tenant entry that cannot possibly work.

    Raised at load time rather than at crawl time: a typo in a region should
    say "region must look like wd1/wd3/wd5", not produce a 404 four minutes
    into a search.
    """


_REGION_RE = re.compile(r"^wd\d+$", re.IGNORECASE)


def validate_workday_entry(entry: dict) -> dict:
    """One tenant entry, checked. Returns it unchanged if it is usable."""
    missing = [key for key in WORKDAY_REQUIRED_KEYS if not str(entry.get(key) or "").strip()]
    if missing:
        raise WorkdayConfigError(
            f"Workday tenant {entry.get('slug') or '(unnamed)'} is missing: "
            + ", ".join(missing)
            + ". A Workday board needs tenant (slug), regional host (region, e.g. wd5) "
            "and site name (site, e.g. External_Career_Site)."
        )
    region = str(entry["region"]).strip()
    if not _REGION_RE.match(region):
        raise WorkdayConfigError(
            f"Workday tenant {entry['slug']}: region {region!r} does not look like a "
            "Workday regional host — expected wd1, wd3, wd5, wd12, …"
        )
    return entry


def load_workday_config(raw: str) -> list[dict]:
    """Workday tenants from a JSON array, for adding one without a code change.

    Accepts the same shape as ``WORKDAY_BOARDS``. Every entry is validated, and
    a bad entry raises rather than being skipped — silently dropping a tenant
    the user deliberately configured is worse than refusing to start.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WorkdayConfigError(f"CAREEROS_WORKDAY_BOARDS is not valid JSON: {exc}") from exc
    if not isinstance(parsed, list):
        raise WorkdayConfigError(
            "CAREEROS_WORKDAY_BOARDS must be a JSON array of "
            '{"slug": …, "name": …, "region": …, "site": …} objects'
        )
    entries = []
    for item in parsed:
        if not isinstance(item, dict):
            raise WorkdayConfigError(f"CAREEROS_WORKDAY_BOARDS entry is not an object: {item!r}")
        entries.append(validate_workday_entry(item))
    return entries


def workday_boards() -> list[BoardEntry]:
    """The configured Workday tenants.

    ``CAREEROS_WORKDAY_BOARDS`` (a JSON array) REPLACES the built-in list when
    set — replaces rather than extends, so a deployment that wants only its own
    tenants gets exactly those, and the built-ins are one copy-paste away.
    """
    raw = os.environ.get("CAREEROS_WORKDAY_BOARDS", "").strip()
    entries = load_workday_config(raw) if raw else list(WORKDAY_BOARDS)
    return [
        BoardEntry(
            b["slug"], b.get("name"), **{k: v for k, v in b.items() if k not in ("slug", "name")}
        )
        for b in entries
    ]
