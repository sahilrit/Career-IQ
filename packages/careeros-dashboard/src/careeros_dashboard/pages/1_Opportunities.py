"""Opportunity page: every application's score, company, job, status,
and status-change timeline.
"""

from __future__ import annotations

import streamlit as st

from careeros_career_brain.models import ApplicationStatus
from careeros_dashboard.data_access import list_applications, primary_brain
from careeros_dashboard.runtime import get_store
from careeros_dashboard.search_actions import generate_application_for_job, search_for_jobs
from careeros_dashboard.theme import badge, inject_theme

st.set_page_config(page_title="Opportunities", page_icon="🎯", layout="wide")

inject_theme()

_STATUS_TONE = {
    ApplicationStatus.DISCOVERED: "mute",
    ApplicationStatus.QUALIFIED: "mute",
    ApplicationStatus.APPLIED: "blue",
    ApplicationStatus.IN_REVIEW: "blue",
    ApplicationStatus.INTERVIEWING: "yellow",
    ApplicationStatus.OFFER: "green",
    ApplicationStatus.ACCEPTED: "green",
    ApplicationStatus.REJECTED: "red",
    ApplicationStatus.WITHDRAWN: "red",
}

store = get_store()
st.title("Opportunities")

brain = primary_brain(store)

if brain is None:
    st.info("Create your Career Brain first, on the Career Brain page.")
    st.stop()

with st.expander("Search for jobs", expanded=False), st.form("search_jobs"):
    keywords_raw = st.text_input("Keywords (comma-separated)")
    remote_only = st.checkbox("Remote only")
    limit = st.number_input("Max results", min_value=1, max_value=100, value=25)
    if st.form_submit_button("Search"):
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        summary = search_for_jobs(
            store, brain.identity.id, keywords=keywords, remote_only=remote_only, limit=limit
        )
        st.success(
            f"Discovered {summary['discovered']} posting(s), {summary['qualified']} qualified."
        )
        st.rerun()

applications = list_applications(store)

if not applications:
    st.info("No applications yet — search for jobs above.")
else:
    for application in applications:
        label = f"{application.job_title} at {application.company_name}"
        with st.expander(label):
            st.markdown(
                badge(application.status.value, _STATUS_TONE.get(application.status, "mute")),
                unsafe_allow_html=True,
            )
            if application.match_score is not None:
                st.write(f"**Score:** {application.match_score:.0%}")
            if application.job_url:
                st.write(f"[Job posting]({application.job_url})")
            if application.notes:
                st.write(f"**Notes:** {application.notes}")
            st.write("**Timeline:**")
            for change in application.history:
                st.markdown(
                    f"{badge(change.status.value, _STATUS_TONE.get(change.status, 'mute'))} "
                    f"<span style='color:#9c9c9d;font-size:13px;'>{change.changed_at}</span>",
                    unsafe_allow_html=True,
                )

            if application.job_url and st.button(
                "Generate resume & cover letter", key=f"gen_{application.id}"
            ):
                package = generate_application_for_job(
                    store, brain.identity.id, application.job_url
                )
                if package is None:
                    st.error("That posting is no longer open — it can't be generated from.")
                else:
                    st.session_state[f"package_{application.id}"] = package

            package = st.session_state.get(f"package_{application.id}")
            if package is not None:
                st.text_area(
                    "Resume", package.resume_text, height=200, key=f"resume_{application.id}"
                )
                st.text_area(
                    "Cover letter", package.cover_letter, height=150, key=f"cover_{application.id}"
                )
                st.download_button(
                    "Download resume (.txt)",
                    package.resume_text,
                    file_name="resume.txt",
                    key=f"dl_resume_{application.id}",
                )
                st.download_button(
                    "Download cover letter (.txt)",
                    package.cover_letter,
                    file_name="cover_letter.txt",
                    key=f"dl_cover_{application.id}",
                )
