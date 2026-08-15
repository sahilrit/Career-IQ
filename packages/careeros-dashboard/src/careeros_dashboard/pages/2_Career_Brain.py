"""Career Brain page: manage identity, skills, experience, education,
certifications, projects, languages, awards, goals, preferences, and
view the portfolio. Single Career Brain per install for now — see
data_access.primary_brain.
"""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.career_brain_actions import (
    add_achievement,
    add_award,
    add_certification,
    add_education,
    add_experience,
    add_goal,
    add_language,
    add_project,
    add_skill,
    get_or_create_brain,
    update_preferences,
    update_summary,
)
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.runtime import get_store
from careeros_dashboard.theme import badge, inject_theme
from careeros_employment_division import build_portfolio_summary, render_portfolio_summary

st.set_page_config(page_title="Career Brain", page_icon="🧠", layout="wide")

inject_theme()

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

with st.expander("Professional summary", expanded=not brain.identity.summary), st.form("summary"):
    summary_text = st.text_area("Summary", value=brain.identity.summary, height=120)
    if st.form_submit_button("Save summary"):
        update_summary(store, brain, summary_text)
        st.rerun()

(
    tab_skills,
    tab_experience,
    tab_education,
    tab_certifications,
    tab_projects,
    tab_languages,
    tab_awards,
    tab_goals,
    tab_preferences,
    tab_portfolio,
) = st.tabs(
    [
        "Skills",
        "Experience",
        "Education",
        "Certifications",
        "Projects",
        "Languages",
        "Awards",
        "Goals",
        "Preferences",
        "Portfolio",
    ]
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

with tab_education:
    st.subheader("Education")
    for education in brain.education:
        span = " — ".join(
            str(d) for d in (education.start_date, education.end_date) if d is not None
        )
        label = f"**{education.credential}**, {education.institution}"
        if span:
            label += f" ({span})"
        st.write(f"- {label}")
        if education.description:
            st.caption(education.description)
    with st.form("add_education"):
        institution = st.text_input("Institution")
        credential = st.text_input("Credential (e.g. Bachelor of Computer Applications)")
        field_of_study = st.text_input("Field of study (optional)")
        edu_start = st.date_input("Start date (optional)", value=None)
        edu_end = st.date_input("End date (optional)", value=None)
        edu_description = st.text_area("Description (optional)")
        if st.form_submit_button("Add education") and institution and credential:
            add_education(
                store,
                brain,
                institution=institution,
                credential=credential,
                field_of_study=field_of_study or None,
                start_date=edu_start,
                end_date=edu_end,
                description=edu_description,
            )
            st.rerun()

with tab_certifications:
    st.subheader("Certifications")
    for certification in brain.certifications:
        label = certification.name
        if certification.issuer:
            label += f" — {certification.issuer}"
        if certification.issued_date:
            label += f" ({certification.issued_date})"
        if certification.credential_url:
            st.write(f"- [{label}]({certification.credential_url})")
        else:
            st.write(f"- {label}")
    with st.form("add_certification"):
        cert_name = st.text_input("Certification name")
        cert_issuer = st.text_input("Issuer (optional)")
        cert_issued = st.date_input("Issued date (optional)", value=None)
        cert_expiration = st.date_input("Expiration date (optional)", value=None)
        cert_url = st.text_input("Credential URL (optional)")
        if st.form_submit_button("Add certification") and cert_name:
            add_certification(
                store,
                brain,
                name=cert_name,
                issuer=cert_issuer or None,
                issued_date=cert_issued,
                expiration_date=cert_expiration,
                credential_url=cert_url or None,
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

with tab_languages:
    st.subheader("Languages")
    for language in brain.languages:
        st.write(f"- {language.name} ({language.proficiency})")
    with st.form("add_language"):
        language_name = st.text_input("Language")
        proficiency = st.selectbox(
            "Proficiency", ["native", "fluent", "professional", "conversational", "basic"]
        )
        if st.form_submit_button("Add language") and language_name:
            add_language(store, brain, language_name, proficiency)
            st.rerun()

with tab_awards:
    st.subheader("Awards")
    for award in brain.awards:
        label = award.title
        if award.issuer:
            label += f" — {award.issuer}"
        if award.date_received:
            label += f" ({award.date_received})"
        st.write(f"- {label}")
        if award.description:
            st.caption(award.description)
    with st.form("add_award"):
        award_title = st.text_input("Award title")
        award_issuer = st.text_input("Issuer (optional)")
        award_date = st.date_input("Date received (optional)", value=None)
        award_description = st.text_area("Description (optional)")
        if st.form_submit_button("Add award") and award_title:
            add_award(
                store,
                brain,
                title=award_title,
                issuer=award_issuer or None,
                date_received=award_date,
                description=award_description,
            )
            st.rerun()

with tab_goals:
    st.subheader("Goals")
    for goal in brain.goals:
        tone, label = ("green", "achieved") if goal.achieved else ("mute", "in progress")
        st.markdown(f"{badge(label, tone)} {goal.description}", unsafe_allow_html=True)
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
