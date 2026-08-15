"""After-tax income: a transparent single-multiplication estimate from
a rate the user supplies themselves — never a computed tax bracket,
never advice.
"""

from __future__ import annotations

DISCLAIMER = "Estimate only, based on a user-supplied rate — not tax advice."


def after_tax_income(total_income: float, effective_tax_rate: float) -> float:
    return total_income * (1 - effective_tax_rate)
