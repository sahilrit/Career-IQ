"""Billing page: the workspace's current plan, what each tier includes,
and checkout links for upgrading."""

from __future__ import annotations

import streamlit as st

from careeros_billing import PLANS, PlanTier
from careeros_dashboard.auth_gate import require_account, single_user_mode
from careeros_dashboard.billing_actions import checkout_link, current_subscription
from careeros_dashboard.theme import inject_theme

st.set_page_config(page_title="Billing", page_icon="💳", layout="wide")

inject_theme()
account = require_account()

st.title("Billing")

if single_user_mode():
    st.info("Single-user install — billing does not apply. Every feature is available.")
    st.stop()

subscription = current_subscription(account.raw_store, account.workspace_id)
active_plan = PLANS[subscription.plan_tier]

st.markdown(f"**Current plan:** {active_plan.name} — ${active_plan.monthly_price_usd:,.0f}/mo")
st.caption(f"Status: {subscription.status.value}")

columns = st.columns(len(PLANS))
for column, tier in zip(columns, PlanTier, strict=True):
    plan = PLANS[tier]
    with column:
        st.markdown(f"### {plan.name}")
        st.markdown(f"**${plan.monthly_price_usd:,.0f}/mo**")
        st.caption(f"{plan.max_workspaces} workspace(s) · {plan.max_team_members} team member(s)")
        for feature in plan.features:
            st.markdown(f"- {feature.replace('_', ' ').capitalize()}")
        if tier == subscription.plan_tier:
            st.success("Your plan")
        elif plan.monthly_price_usd > active_plan.monthly_price_usd:
            link = checkout_link(tier)
            if link:
                st.link_button(f"Upgrade to {plan.name}", link, width="stretch")
            else:
                st.caption("Contact us to upgrade — checkout link not configured.")

st.divider()
st.caption(
    "Payments are handled by Stripe checkout. After paying, your plan is "
    "activated within a few hours; contact support if it takes longer."
)
