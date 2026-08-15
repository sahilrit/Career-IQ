"""Tests for estimate_roi."""

from __future__ import annotations

from careeros_audit_proposal_engine import ROIInputs, estimate_roi
from careeros_audit_proposal_engine.roi_estimate import DISCLAIMER


def _inputs() -> ROIInputs:
    return ROIInputs(monthly_visitors=10_000, conversion_rate=0.02, average_order_value=50.0)


def test_current_monthly_revenue_is_visitors_times_rate_times_aov():
    estimate = estimate_roi(_inputs(), finding_count=0)
    assert estimate.current_monthly_revenue == 10_000 * 0.02 * 50.0


def test_zero_findings_means_zero_uplift():
    estimate = estimate_roi(_inputs(), finding_count=0)
    assert estimate.assumed_uplift_pct == 0.0
    assert estimate.projected_additional_monthly_revenue == 0.0


def test_uplift_scales_with_finding_count():
    estimate = estimate_roi(_inputs(), finding_count=3, uplift_per_finding_pct=0.02)
    assert estimate.assumed_uplift_pct == 0.06


def test_uplift_is_capped_at_max():
    estimate = estimate_roi(_inputs(), finding_count=100, max_uplift_pct=0.30)
    assert estimate.assumed_uplift_pct == 0.30


def test_annual_is_twelve_times_monthly():
    estimate = estimate_roi(_inputs(), finding_count=5)
    assert estimate.projected_additional_annual_revenue == (
        estimate.projected_additional_monthly_revenue * 12
    )


def test_disclaimer_is_present():
    estimate = estimate_roi(_inputs(), finding_count=1)
    assert estimate.disclaimer == DISCLAIMER
