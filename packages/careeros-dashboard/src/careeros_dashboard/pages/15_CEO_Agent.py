"""CEO Agent page: log how each division is performing, and get a
recommended split of your effort across employment, freelance,
networking, and personal brand."""

from __future__ import annotations

import streamlit as st

from careeros_ceo_agent import (
    AllocationPlanRepository,
    CEOAgentDivision,
    PerformanceInput,
    PerformanceInputRepository,
    ResourceCategory,
)
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import inject_theme

st.set_page_config(page_title="CEO Agent", page_icon="🧭", layout="wide")

inject_theme()
account = require_account()
division = CEOAgentDivision(
    PerformanceInputRepository(account.store), AllocationPlanRepository(account.store)
)

st.title("CEO Agent")
st.caption("Where should your effort go this week? Log recent results, then compute an allocation.")

with st.form("perf"):
    cols = st.columns(3)
    category = cols[0].selectbox("Division", [c.value for c in ResourceCategory])
    metric_name = cols[1].text_input("What you measured", value="results")
    value = cols[2].number_input("Value / score", min_value=0.0, step=1.0, value=1.0)
    if st.form_submit_button("Log result"):
        division.record_performance(
            PerformanceInput(
                category=ResourceCategory(category),
                metric_name=metric_name or "results",
                value=value,
                source="dashboard",
            )
        )
        st.rerun()

if st.button("Compute recommended allocation", type="primary"):
    division.compute_allocation()
    st.rerun()

plan = division.latest_allocation()
if plan is None:
    st.info("Log a few results above, then compute an allocation.")
else:
    st.subheader("Recommended effort split")
    cols = st.columns(len(plan.allocations))
    for column, (category_key, share) in zip(cols, plan.allocations.items(), strict=True):
        label = category_key.value if hasattr(category_key, "value") else str(category_key)
        column.metric(label.replace("_", " ").title(), f"{share:.0%}")
    st.caption(plan.disclaimer)
