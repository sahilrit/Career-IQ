"""Career Brain page: manage identity, skills, experience,
achievements, projects, goals, preferences, and view the portfolio.
Single Career Brain per install for now — see data_access.primary_brain.
"""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.career_brain_actions import (
    add_achievement,
    add_experience,
    add_goal,
    add_project,
    add_skill,
    get_or_create_brain,
    update_preferences,
)
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.runtime import get_store
from careeros_employment_division import build_portfolio_summary, render_portfolio_summary

st.set_page_config(page_title="Career Brain", page_icon="🧠", layout="wide")

store = get_store()
st.title("Career Brain")

brain = primary_brain(store)

if brain is None:
    st.subheader("Create your Career Brain")
    with st.form("create_brain"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        submitted = st.form_submit_button("Create")
    if submitted and full_name and email:
        get_or_create_brain(store, full_name=full_name, email=email)
        st.rerun()
    st.stop()

st.caption(f"{brain.identity.full_name} — {brain.identity.email}")

tab_skills, tab_experience, tab_projects, tab_goals, tab_preferences, tab_portfolio = st.tabs(
    ["Skills", "Experience", "Projects", "Goals", "Preferences", "Portfolio"]
)

with tab_skills:
    st.subheader("Skills")
    for skill in brain.skills:
        st.write(f"- {skill.name} (proficiency {skill.proficiency}/5)")
    with st.form("add_skill"):
        skill_name = st.text_input("Skill name")
        proficiency = st.slider("Proficiency", 1, 5, 3)
        if st.form_submit_button("Add skill") and skill_name:
            add_skill(store, brain, skill_name, proficiency)
            st.rerun()

with tab_experience:
    st.subheader("Experience")
    for experience in brain.experiences:
        with st.expander(f"{experience.title} at {experience.company_name}"):
            for achievement in experience.achievements:
                suffix = f" ({achievement.metric})" if achievement.metric else ""
                st.write(f"- {achievement.description}{suffix}")
            with st.form(f"add_achievement_{experience.id}"):
                description = st.text_input("Achievement", key=f"ach_desc_{experience.id}")
                metric = st.text_input("Metric (optional)", key=f"ach_metric_{experience.id}")
                if st.form_submit_button("Add achievement") and description:
                    add_achievement(
                        store, brain, experience.id, description=description, metric=metric or None
                    )
                    st.rerun()
    with st.form("add_experience"):
        company_name = st.text_input("Company")
        title = st.text_input("Title")
        start_date = st.date_input("Start date", value=None)
        end_date = st.date_input("End date (leave blank if current)", value=None)
        description = st.text_area("Description")
        if st.form_submit_button("Add experience") and company_name and title and start_date:
            add_experience(
                store,
                brain,
                company_name=company_name,
                title=title,
                start_date=start_date,
                end_date=end_date,
                description=description,
            )
            st.rerun()

with tab_projects:
    st.subheader("Projects")
    for project in brain.projects:
        st.write(f"- **{project.name}**: {project.description}")
    with st.form("add_project"):
        project_name = st.text_input("Project name")
        project_description = st.text_area("Project description")
        project_url = st.text_input("URL (optional)")
        skills_raw = st.text_input("Skills used (comma-separated)")
        if st.form_submit_button("Add project") and project_name:
            skills_used = [s.strip() for s in skills_raw.split(",") if s.strip()]
            add_project(
                store,
                brain,
                name=project_name,
                description=project_description,
                url=project_url or None,
                skills_used=skills_used,
            )
            st.rerun()

with tab_goals:
    st.subheader("Goals")
    for goal in brain.goals:
        status_icon = "✅" if goal.achieved else "⬜"
        st.write(f"{status_icon} {goal.description}")
    with st.form("add_goal"):
        goal_description = st.text_input("Goal")
        if st.form_submit_button("Add goal") and goal_description:
            add_goal(store, brain, goal_description)
            st.rerun()

with tab_preferences:
    st.subheader("Preferences")
    with st.form("preferences"):
        titles_raw = st.text_input(
            "Desired titles (comma-separated)", value=", ".join(brain.preferences.desired_titles)
        )
        remote_only = st.checkbox("Remote only", value=brain.preferences.remote_only)
        if st.form_submit_button("Save preferences"):
            desired_titles = [t.strip() for t in titles_raw.split(",") if t.strip()]
            update_preferences(store, brain, desired_titles=desired_titles, remote_only=remote_only)
            st.rerun()

with tab_portfolio:
    st.subheader("Portfolio")
    summary = build_portfolio_summary(brain)
    st.text(render_portfolio_summary(summary))
