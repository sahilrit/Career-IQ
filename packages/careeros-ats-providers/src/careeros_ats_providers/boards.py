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


def workday_boards() -> list[BoardEntry]:
    return [
        BoardEntry(
            b["slug"], b.get("name"), **{k: v for k, v in b.items() if k not in ("slug", "name")}
        )
        for b in WORKDAY_BOARDS
    ]
