"""careeros_arbeitnow_provider: a second FIND_JOBS provider, backed by
Arbeitnow's free public job board API — no API key or paid plan
required. Proves the FIND_JOBS SDK generalizes beyond RemoteOK without
any change to careeros_job_providers itself.
"""

from careeros_arbeitnow_provider.client import (
    ARBEITNOW_API_URL,
    ArbeitnowTransport,
    HttpxArbeitnowTransport,
)
from careeros_arbeitnow_provider.parser import parse_job_entry
from careeros_arbeitnow_provider.provider import ArbeitnowProvider

__all__ = [
    "ARBEITNOW_API_URL",
    "ArbeitnowProvider",
    "ArbeitnowTransport",
    "HttpxArbeitnowTransport",
    "parse_job_entry",
]
