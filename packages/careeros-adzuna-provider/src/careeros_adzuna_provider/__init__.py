"""careeros_adzuna_provider: FIND_JOBS backed by Adzuna's official API.

Adzuna aggregates adverts from job boards, ATS feeds and employer sites
across 20+ countries and publishes them through a documented, keyed REST
API — the highest-volume source on our list that comes with a licence to
use it. Register free at https://developer.adzuna.com and set
``ADZUNA_APP_ID`` / ``ADZUNA_APP_KEY``; without them the provider reports
itself unavailable and the rest of discovery carries on.
"""

from careeros_adzuna_provider.client import (
    ADZUNA_API_ROOT,
    ADZUNA_APP_ID_ENV_VAR,
    ADZUNA_APP_KEY_ENV_VAR,
    MAX_RESULTS_PER_PAGE,
    AdzunaTransport,
    HttpxAdzunaTransport,
    credentials,
)
from careeros_adzuna_provider.countries import (
    COUNTRY_TOKENS,
    DEFAULT_COUNTRY,
    country_for_locations,
)
from careeros_adzuna_provider.parser import PROVIDER_ID, is_job_entry, parse_job_entry
from careeros_adzuna_provider.provider import AdzunaProvider

__all__ = [
    "ADZUNA_API_ROOT",
    "ADZUNA_APP_ID_ENV_VAR",
    "ADZUNA_APP_KEY_ENV_VAR",
    "COUNTRY_TOKENS",
    "DEFAULT_COUNTRY",
    "MAX_RESULTS_PER_PAGE",
    "PROVIDER_ID",
    "AdzunaProvider",
    "AdzunaTransport",
    "HttpxAdzunaTransport",
    "country_for_locations",
    "credentials",
    "is_job_entry",
    "parse_job_entry",
]
