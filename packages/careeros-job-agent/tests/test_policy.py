"""Tests for QualificationPolicy."""

from __future__ import annotations

from careeros_job_agent import QualificationPolicy


def test_score_at_or_above_threshold_is_qualified():
    policy = QualificationPolicy(min_match_score=0.6)
    assert policy.is_qualified(0.6) is True
    assert policy.is_qualified(0.9) is True


def test_score_below_threshold_is_not_qualified():
    policy = QualificationPolicy(min_match_score=0.6)
    assert policy.is_qualified(0.59) is False


def test_missing_score_is_not_qualified():
    policy = QualificationPolicy(min_match_score=0.6)
    assert policy.is_qualified(None) is False


def test_default_threshold():
    policy = QualificationPolicy()
    assert policy.min_match_score == 0.6
