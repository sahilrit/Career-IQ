"""Industry performance: how many freelance prospects came from each
industry — Company.industry (Phase 31) is the only real industry field
in the platform today; employment Applications carry no industry field,
so this covers the freelance side only rather than inventing one.
"""

from __future__ import annotations

from careeros_client_acquisition import Company

_UNKNOWN_INDUSTRY = "unknown"


def compute_industry_performance(companies: list[Company]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for company in companies:
        key = company.industry or _UNKNOWN_INDUSTRY
        counts[key] = counts.get(key, 0) + 1
    return counts
