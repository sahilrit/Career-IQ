"""Adzuna is a per-country API: the country is part of the URL path, not a
filter, so a search has to pick one before it runs.

We infer it from the requested location. Nothing stated means Great Britain,
which is Adzuna's largest index and its default in their own docs.
"""

from __future__ import annotations

DEFAULT_COUNTRY = "gb"

#: Every country Adzuna serves, keyed by the tokens a user is likely to type.
COUNTRY_TOKENS: dict[str, str] = {
    "australia": "au",
    "austria": "at",
    "belgium": "be",
    "brazil": "br",
    "canada": "ca",
    "france": "fr",
    "germany": "de",
    "india": "in",
    "italy": "it",
    "mexico": "mx",
    "netherlands": "nl",
    "new zealand": "nz",
    "poland": "pl",
    "singapore": "sg",
    "south africa": "za",
    "spain": "es",
    "switzerland": "ch",
    "united kingdom": "gb",
    "great britain": "gb",
    "england": "gb",
    "scotland": "gb",
    "wales": "gb",
    "uk": "gb",
    "united states": "us",
    "usa": "us",
    "us": "us",
    "america": "us",
}

#: Major cities, so "Bengaluru" resolves without the user naming the country.
CITY_TOKENS: dict[str, str] = {
    "london": "gb",
    "manchester": "gb",
    "birmingham": "gb",
    "edinburgh": "gb",
    "new york": "us",
    "san francisco": "us",
    "chicago": "us",
    "austin": "us",
    "seattle": "us",
    "boston": "us",
    "toronto": "ca",
    "vancouver": "ca",
    "sydney": "au",
    "melbourne": "au",
    "berlin": "de",
    "munich": "de",
    "hamburg": "de",
    "paris": "fr",
    "amsterdam": "nl",
    "madrid": "es",
    "barcelona": "es",
    "milan": "it",
    "rome": "it",
    "zurich": "ch",
    "vienna": "at",
    "brussels": "be",
    "warsaw": "pl",
    "singapore": "sg",
    "auckland": "nz",
    "mumbai": "in",
    "delhi": "in",
    "new delhi": "in",
    "bengaluru": "in",
    "bangalore": "in",
    "hyderabad": "in",
    "chennai": "in",
    "pune": "in",
    "gurugram": "in",
    "gurgaon": "in",
    "noida": "in",
    "kolkata": "in",
    "sao paulo": "br",
    "mexico city": "mx",
    "johannesburg": "za",
    "cape town": "za",
}


def country_for_locations(locations: list[str]) -> str:
    """The Adzuna country code for the first location we recognise.

    Countries are checked before cities so "Birmingham, United States" does
    not resolve to Great Britain on the strength of the city name.
    """
    for raw in locations:
        # Whole-word tokens, so a country key like "us" matches the token "us"
        # but never a substring of "Belarus" or "Aarhus". A multi-word key like
        # "united states" matches only when all its words are present.
        words = set("".join(c if c.isalnum() else " " for c in str(raw).lower()).split())
        if not words:
            continue
        for token, code in COUNTRY_TOKENS.items():
            if set(token.split()) <= words:
                return code
        for token, code in CITY_TOKENS.items():
            if set(token.split()) <= words:
                return code
    return DEFAULT_COUNTRY
