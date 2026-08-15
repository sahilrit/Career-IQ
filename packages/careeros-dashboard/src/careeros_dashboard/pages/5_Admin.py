"""Admin console: customer list, plan activation, and top-line metrics.

Visible only to operators — emails listed in ``CAREEROS_ADMIN_EMAILS``.
Plan activation here is the manual fulfillment step after a Stripe
checkout (see billing_actions)."""

from __future__ import annotations

import streamlit as st

from careeros_billing import PLANS, PlanTier
from careeros_dashboard.auth_gate import require_account, single_user_mode
from careeros_dashboard.billing_actions import current_subscription, set_plan
from careeros_dashboard.theme import inject_theme
from careeros_tenancy import TenancyRepository

st.set_page_config(page_title="Admin", page_icon="🛠️", layout="wide")

inject_theme()
account = require_account()

st.title("Admin")

if single_user_mode():
    st.info("Single-user install — there is nothing to administer.")
    st.stop()

if not account.is_admin:
    st.error("You don't have access to this page.")
    st.stop()

tenancy = TenancyRepository(account.raw_store)
users = tenancy.list_users()

rows = []
for user in users:
    for membership in tenancy.workspaces_for_user(user.id):
        subscription = current_subscription(account.raw_store, membership.workspace_id)
        rows.append(
            {
                "Name": user.full_name,
                "Email": user.email,
                "Role": membership.role.value,
                "Workspace": membership.workspace_id,
                "Plan": subscription.plan_tier.value,
                "Status": subscription.status.value,
                "Joined": f"{user.created_at:%Y-%m-%d}",
            }
        )

paying = [row for row in rows if row["Plan"] != PlanTier.FREE.value]
mrr = sum(PLANS[PlanTier(row["Plan"])].monthly_price_usd for row in paying)

metric_cols = st.columns(3)
metric_cols[0].metric("Accounts", len(users))
metric_cols[1].metric("Paying workspaces", len(paying))
metric_cols[2].metric("MRR", f"${mrr:,.0f}")

st.subheader("Customers")
if rows:
    st.dataframe(rows, width="stretch")
else:
    st.caption("No customers yet.")

st.divider()
st.subheader("Activate a plan")
st.caption("Manual fulfillment after a Stripe payment: pick the workspace and its new tier.")
if rows:
    with st.form("activate_plan"):
        workspace_options = {
            f"{row['Email']} — {row['Workspace'][:8]}… ({row['Plan']})": row["Workspace"]
            for row in rows
        }
        chosen = st.selectbox("Workspace", list(workspace_options))
        tier = st.selectbox("Plan tier", [tier.value for tier in PlanTier])
        if st.form_submit_button("Set plan"):
            set_plan(account.raw_store, workspace_options[chosen], PlanTier(tier))
            st.success(f"Plan set to {tier}.")
            st.rerun()
