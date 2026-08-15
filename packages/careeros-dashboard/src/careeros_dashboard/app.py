"""CareerOS Dashboard — the main product UI.

Run with:

    streamlit run src/careeros_dashboard/app.py

Reads the same local database the CLI writes to (``.careeros/data/careeros.db``
by default, or ``$CAREEROS_DATA_DIR``) — nothing here is sample data.
"""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.data_access import build_dashboard_summary, primary_brain
from careeros_dashboard.runtime import get_store

st.set_page_config(page_title="CareerOS", page_icon="🧭", layout="wide")


def main() -> None:
    store = get_store()
    st.title("CareerOS")

    brain = primary_brain(store)
    if brain is None:
        st.info("No Career Brain yet — create one on the Career Brain page.")
    else:
        st.caption(f"{brain.identity.full_name} — {brain.identity.headline or 'No headline set'}")

    summary = build_dashboard_summary(store)

    top_row = st.columns(4)
    top_row[0].metric("Applications", summary.application_count)
    top_row[1].metric("Upcoming interviews", summary.upcoming_interview_count)
    top_row[2].metric("Offers", summary.offer_count)
    top_row[3].metric("Freelance prospects", summary.prospect_count)

    bottom_row = st.columns(4)
    bottom_row[0].metric("Active clients", summary.active_client_count)
    bottom_row[1].metric("Total income", f"${summary.total_income:,.0f}")
    bottom_row[2].metric("Network contacts", summary.network_contact_count)
    bottom_row[3].metric("Pending tasks", len(summary.pending_tasks))

    if summary.pending_tasks:
        st.subheader("Pending tasks")
        for task in summary.pending_tasks:
            st.write(f"- {task}")
    else:
        st.subheader("Pending tasks")
        st.write("Nothing pending.")


main()
