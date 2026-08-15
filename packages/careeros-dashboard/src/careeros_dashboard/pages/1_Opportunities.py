"""Opportunity page: every application's score, company, job, status,
and status-change timeline.
"""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.data_access import list_applications
from careeros_dashboard.runtime import get_store

st.set_page_config(page_title="Opportunities", page_icon="🎯", layout="wide")

store = get_store()
st.title("Opportunities")

applications = list_applications(store)

if not applications:
    st.info("No applications yet.")
else:
    for application in applications:
        label = (
            f"{application.job_title} at {application.company_name} — {application.status.value}"
        )
        with st.expander(label):
            st.write(f"**Status:** {application.status.value}")
            if application.match_score is not None:
                st.write(f"**Score:** {application.match_score:.0%}")
            if application.job_url:
                st.write(f"[Job posting]({application.job_url})")
            if application.notes:
                st.write(f"**Notes:** {application.notes}")
            st.write("**Timeline:**")
            for change in application.history:
                st.write(f"- {change.status.value} at {change.changed_at}")
