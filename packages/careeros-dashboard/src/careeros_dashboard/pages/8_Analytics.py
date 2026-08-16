"""Analytics page: your career funnel, freelance funnel, and Career ROI —
computed over everything the rest of the product records."""

from __future__ import annotations

import streamlit as st

from careeros_analytics import AnalyticsDivision
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import inject_theme

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

inject_theme()
account = require_account()
analytics = AnalyticsDivision(account.store)

st.title("Analytics")

funnel = analytics.application_funnel()
st.subheader("Job application funnel")
cols = st.columns(6)
cols[0].metric("Discovered", funnel.discovered_count)
cols[1].metric("Applied", funnel.applied_count)
cols[2].metric("Responses", funnel.response_count)
cols[3].metric("Interviews", funnel.interview_count)
cols[4].metric("Offers", funnel.offer_count)
cols[5].metric("Accepted", funnel.accepted_count)
rate_cols = st.columns(4)
for column, (label, value) in zip(
    rate_cols,
    [
        ("Response rate", funnel.response_rate),
        ("Interview rate", funnel.interview_rate),
        ("Offer rate", funnel.offer_rate),
        ("Acceptance rate", funnel.acceptance_rate),
    ],
    strict=True,
):
    column.metric(label, "—" if value is None else f"{value:.0%}")

st.divider()
st.subheader("Freelance funnel")
freelance = analytics.freelance_funnel()
fcols = st.columns(6)
fcols[0].metric("Leads", freelance.lead_count)
fcols[1].metric("Outreach", freelance.outreach_count)
fcols[2].metric("Proposals", freelance.proposal_count)
fcols[3].metric("Calls", freelance.call_count)
fcols[4].metric("Clients", freelance.client_count)
fcols[5].metric("Revenue", f"${freelance.total_revenue:,.0f}")

st.divider()
st.subheader("Career ROI")
roi = analytics.career_roi()
rcols = st.columns(4)
rcols[0].metric("Salary income", f"${roi.salary_income:,.0f}")
rcols[1].metric("Freelance income", f"${roi.freelance_income:,.0f}")
rcols[2].metric("Equity value", f"${roi.equity_value:,.0f}")
rcols[3].metric("Financial total", f"${roi.financial_total:,.0f}")
st.caption(roi.disclaimer)

platform = analytics.platform_performance()
if platform:
    st.divider()
    st.subheader("By source")
    st.dataframe(
        [
            {
                "Source": name,
                "Applied": metrics.applied_count,
                "Interviews": metrics.interview_count,
                "Offers": metrics.offer_count,
            }
            for name, metrics in platform.items()
        ],
        width="stretch",
    )
