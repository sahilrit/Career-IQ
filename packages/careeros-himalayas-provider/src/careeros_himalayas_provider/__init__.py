"""careeros_himalayas_provider: a third FIND_JOBS provider, backed by
Himalayas' free public remote-jobs API — no API key or paid plan
required. Adds real non-tech posting volume (marketing, sales, ops)
to the discovery pool.
"""

from careeros_himalayas_provider.client import (
    HIMALAYAS_API_URL,
    HimalayasTransport,
    HttpxHimalayasTransport,
)
from careeros_himalayas_provider.parser import is_job_entry, parse_job_entry
from careeros_himalayas_provider.provider import HimalayasProvider

__all__ = [
    "HIMALAYAS_API_URL",
    "HimalayasProvider",
    "HimalayasTransport",
    "HttpxHimalayasTransport",
    "is_job_entry",
    "parse_job_entry",
]
