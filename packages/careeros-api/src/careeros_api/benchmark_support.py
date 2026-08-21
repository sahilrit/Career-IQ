"""Compensation benchmark for negotiation prep. This is a transparent ESTIMATE,
not scraped market data: when the user supplies a comparable salary it does
honest math around that anchor; otherwise it gives a clearly-labelled rough
USD band from role family + seniority. Always carries a disclaimer."""

from __future__ import annotations

from typing import Any

# Broad USD midpoints by role family — deliberately coarse; only used as a
# fallback when the user gives no comparable salary of their own.
_ROLE_BASE = {
    "software": 130000,
    "engineer": 125000,
    "developer": 120000,
    "data": 120000,
    "product": 130000,
    "design": 100000,
    "designer": 100000,
    "growth": 100000,
    "marketing": 90000,
    "sales": 85000,
    "account": 75000,
    "finance": 105000,
    "operations": 90000,
    "analyst": 85000,
    "director": 165000,
    "manager": 115000,
}
_DEFAULT_BASE = 90000
_LEVEL_MULT = {"entry": 0.7, "mid": 1.0, "senior": 1.35, "lead": 1.75}
_DISCLAIMER = (
    "Estimate for negotiation prep, not financial advice — verify against sources "
    "like Levels.fyi, Glassdoor, or local salary guides for your market."
)


def infer_level(years_experience: float) -> str:
    if years_experience < 2:
        return "entry"
    if years_experience < 5:
        return "mid"
    if years_experience < 9:
        return "senior"
    return "lead"


def _role_family(role: str) -> tuple[str, int]:
    lowered = role.lower()
    for keyword, base in _ROLE_BASE.items():
        if keyword in lowered:
            return keyword, base
    return "general", _DEFAULT_BASE


def compensation_benchmark(
    *,
    role: str,
    level: str | None,
    years_experience: float,
    anchor_salary: int | None,
    min_salary: int | None,
    currency: str,
) -> dict[str, Any]:
    seniority = level if level in _LEVEL_MULT else infer_level(years_experience)
    family, base_usd = _role_family(role)

    if anchor_salary and anchor_salary > 0:
        mid = anchor_salary
        low, high = round(mid * 0.95), round(mid * 1.15)
        used_currency = currency or "USD"
        confidence = "grounded in the comparable salary you provided"
        rationale = (
            f"Anchored on your comparable of {used_currency} {anchor_salary:,} for a "
            f"{seniority}-level {family} role; range is a typical negotiation band around it."
        )
    else:
        mid = round(base_usd * _LEVEL_MULT[seniority])
        low, high = round(mid * 0.9), round(mid * 1.25)
        used_currency = "USD"
        confidence = "rough USD estimate — add a comparable salary for a sharper, local range"
        rationale = (
            f"Rough {family}-family midpoint at {seniority} level (~{years_experience:.0f} yrs "
            f"experience). No local anchor provided, so this is US-market USD."
        )

    suggested_ask = max(high, min_salary or 0)
    return {
        "currency": used_currency,
        "low": low,
        "mid": mid,
        "high": high,
        "suggested_ask": suggested_ask,
        "seniority": seniority,
        "role_family": family,
        "confidence": confidence,
        "rationale": rationale,
        "disclaimer": _DISCLAIMER,
    }
