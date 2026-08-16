"""Autopilot page: run the fully autonomous apply loop and see exactly
what it did — every submission, every handoff, with reasons."""

from __future__ import annotations

import streamlit as st

from careeros_autopilot import list_autopilot_runs, run_autopilot_cycle
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.search_actions import default_provider_registry
from careeros_dashboard.theme import badge, inject_theme

st.set_page_config(page_title="Autopilot", page_icon="🤖", layout="wide")

inject_theme()
account = require_account()

st.title("Autopilot")
st.caption(
    "Fully autonomous applying: discovers new matching jobs, navigates to each "
    "application form, fills it from your Career Brain, and submits — no clicks "
    "needed. Anything it can't do safely (captchas, sites that require login) "
    "is held for you with the reason shown below; it never bypasses those."
)

brain = primary_brain(account.store)
if brain is None:
    st.info("Create your Career Brain first, on the Career Brain page.")
    st.stop()

default_keywords = ", ".join(
    brain.preferences.desired_titles or ["performance marketing", "ppc", "digital marketing"]
)

with st.form("autopilot_run"):
    keywords_raw = st.text_input("Search keywords (comma-separated)", value=default_keywords)
    remote_only = st.checkbox("Remote only", value=True)
    if st.form_submit_button("Run autopilot cycle now", type="primary"):
        keywords = [keyword.strip() for keyword in keywords_raw.split(",") if keyword.strip()]
        with st.spinner(
            "Autopilot running: discovering, qualifying, and submitting — this can "
            "take several minutes..."
        ):
            report = run_autopilot_cycle(
                account.store,
                provider_registry=default_provider_registry(),
                keywords=keywords,
                remote_only=remote_only,
            )
        st.success(
            f"Cycle done: {report['discovered']} new job(s) discovered, "
            f"{report['newly_qualified']} newly qualified, "
            f"{report['submitted']} application(s) submitted autonomously."
        )
        st.rerun()

st.caption(
    "To run this on a schedule with no clicks at all, keep the daemon running: "
    "`uv run python scripts/autopilot_daemon.py --workspace-id <your id>` "
    "(see the Admin page for your workspace id)."
)

st.divider()
st.subheader("Run history")
runs = list_autopilot_runs(account.store)
if not runs:
    st.caption("No autopilot runs yet.")
for run in runs[:10]:
    header = (
        f"{run['ran_at'][:16].replace('T', ' ')} — "
        f"{run['submitted']} submitted / {run['qualified_total']} qualified"
    )
    with st.expander(header, expanded=run is runs[0]):
        st.caption(f"Keywords: {', '.join(run.get('keywords', []))}")
        for outcome in run.get("outcomes", []):
            tone = "green" if outcome["submitted"] else "yellow"
            label = "submitted" if outcome["submitted"] else "held for you"
            st.markdown(
                f"{badge(label, tone)} **{outcome['job_title']}** @ "
                f"{outcome['company_name']}"
                + ("" if outcome["submitted"] else f" — {outcome['reason']}"),
                unsafe_allow_html=True,
            )
