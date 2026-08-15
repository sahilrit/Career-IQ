"""Tests for qualify() and score_company_opportunity()."""

from __future__ import annotations

from careeros_client_acquisition import IdealClientProfile, ProblemSignal, SignalType
from careeros_client_acquisition.qualification import qualify
from careeros_client_acquisition.scoring import score_company_opportunity


def _signal(kind: SignalType = SignalType.NO_HTTPS) -> ProblemSignal:
    return ProblemSignal(signal_type=kind, detail="detail")


def test_qualify_passes_when_signal_count_meets_threshold(company):
    profile = IdealClientProfile(min_signal_count=1)
    assert qualify(company, [_signal()], profile) is True


def test_qualify_fails_when_no_signals_and_threshold_requires_one(company):
    profile = IdealClientProfile(min_signal_count=1)
    assert qualify(company, [], profile) is False


def test_qualify_fails_when_industry_does_not_match(company):
    profile = IdealClientProfile(industries=["healthcare"], min_signal_count=0)
    assert qualify(company, [], profile) is False


def test_qualify_passes_when_industry_matches(company):
    profile = IdealClientProfile(industries=["retail"], min_signal_count=0)
    assert qualify(company, [], profile) is True


def test_score_scales_with_signal_count():
    assert score_company_opportunity([]) == 0.0
    assert score_company_opportunity([_signal(), _signal()]) == 40.0


def test_score_caps_at_100():
    signals = [_signal() for _ in range(10)]
    assert score_company_opportunity(signals) == 100.0
