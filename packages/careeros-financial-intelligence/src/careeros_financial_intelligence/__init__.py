"""careeros_financial_intelligence: tracks salary/freelance/client
income, effective hourly rate, and income trends, and compares
full-time vs. freelance vs. combined strategy.
"""

from careeros_financial_intelligence.exceptions import FinancialIntelligenceError
from careeros_financial_intelligence.financial_intelligence_division import (
    FinancialIntelligenceDivision,
)
from careeros_financial_intelligence.hourly_rate import calculate_effective_hourly_rate
from careeros_financial_intelligence.income import IncomeRecord, IncomeRepository, IncomeSource
from careeros_financial_intelligence.income_trends import (
    MonthlyTotal,
    TrendDirection,
    detect_trend,
    monthly_totals,
)
from careeros_financial_intelligence.strategy_comparison import (
    FinancialComparison,
    annualized_freelance_income,
    compare_strategies,
)
from careeros_financial_intelligence.tax import after_tax_income

__all__ = [
    "FinancialComparison",
    "FinancialIntelligenceDivision",
    "FinancialIntelligenceError",
    "IncomeRecord",
    "IncomeRepository",
    "IncomeSource",
    "MonthlyTotal",
    "TrendDirection",
    "after_tax_income",
    "annualized_freelance_income",
    "calculate_effective_hourly_rate",
    "compare_strategies",
    "detect_trend",
    "monthly_totals",
]
