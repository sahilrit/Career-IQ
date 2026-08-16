"""Interview prep page: generate likely questions, STAR prompts from your
real achievements, and a one-page briefing for a specific role."""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.theme import inject_theme
from careeros_interview_intelligence import (
    generate_one_page_briefing,
    generate_questions,
    render_one_page_briefing,
)

st.set_page_config(page_title="Interview Prep", page_icon="🎤", layout="wide")

inject_theme()
account = require_account()

st.title("Interview prep")

brain = primary_brain(account.store)
if brain is None:
    st.info("Create your Career Brain first, on the Career Brain page.")
    st.stop()

with st.form("interview_prep"):
    job_title = st.text_input("Role you're interviewing for")
    company_name = st.text_input("Company")
    job_description = st.text_area("Paste the job description (optional)", height=140)
    submitted = st.form_submit_button("Generate prep")

if submitted and job_title and company_name:
    questions = generate_questions(
        brain, job_title=job_title, company_name=company_name, job_description=job_description
    )
    briefing = generate_one_page_briefing(
        brain, job_title=job_title, company_name=company_name, job_description=job_description
    )

    tab_q, tab_star, tab_brief = st.tabs(
        ["Likely questions", "Your STAR stories", "One-page brief"]
    )
    with tab_q:
        st.markdown("**Role-specific**")
        for question in questions.role_specific:
            st.write(f"- {question}")
        st.markdown("**Technical**")
        for question in questions.technical:
            st.write(f"- {question}")
        st.markdown("**About the company**")
        for question in questions.company_specific:
            st.write(f"- {question}")
    with tab_star:
        st.caption("Answer these with your own real achievements (already pulled in):")
        for prompt in questions.star_prompts:
            suffix = f" — _{prompt.metric}_" if prompt.metric else ""
            st.write(f"**{prompt.question}**")
            st.write(f"→ {prompt.achievement_description}{suffix}")
    with tab_brief:
        briefing_text = render_one_page_briefing(briefing)
        st.text(briefing_text)
        st.download_button(
            "Download briefing (.txt)",
            briefing_text,
            file_name=f"briefing-{company_name}.txt",
        )
