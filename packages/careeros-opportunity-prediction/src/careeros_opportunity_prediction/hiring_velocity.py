"""Hiring velocity: the one prediction signal computable directly from
data the platform already collects — job posting dates for a company,
already gathered by Phase 6-8's job discovery pipeline — rather than a
manually-supplied observation. Counting real postings in a real window
avoids fabricating a "hiring surge" that isn't actually happening.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_opportunity_prediction.signal import PredictionSignal, SignalType

_DEFAULT_WINDOW_DAYS = 90
_DEFAULT_MIN_POSTINGS = 3


def compute_hiring_velocity_signal(
    company_id: str,
    posted_dates: list[datetime],
    *,
    window_days: int = _DEFAULT_WINDOW_DAYS,
    min_postings: int = _DEFAULT_MIN_POSTINGS,
    now: datetime | None = None,
) -> PredictionSignal | None:
    current_time = now or datetime.now(UTC)
    cutoff = current_time - timedelta(days=window_days)
    recent = [dt for dt in posted_dates if dt >= cutoff]

    if len(recent) < min_postings:
        return None

    return PredictionSignal(
        company_id=company_id,
        signal_type=SignalType.HIRING_VELOCITY,
        detail=f"{len(recent)} job postings in the last {window_days} days",
        observed_at=current_time,
    )
