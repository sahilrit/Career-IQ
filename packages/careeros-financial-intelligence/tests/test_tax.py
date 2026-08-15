"""Tests for after_tax_income."""

from __future__ import annotations

from careeros_financial_intelligence import after_tax_income


def test_applies_the_rate():
    assert after_tax_income(100_000, 0.25) == 75_000


def test_zero_rate_leaves_income_unchanged():
    assert after_tax_income(100_000, 0.0) == 100_000
