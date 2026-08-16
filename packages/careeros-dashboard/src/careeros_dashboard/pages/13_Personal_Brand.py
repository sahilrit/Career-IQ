"""Personal Brand page: turn one of your projects into a case study and
ready-to-post content — LinkedIn post, X thread, portfolio page, blog."""

from __future__ import annotations

import streamlit as st

from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.theme import inject_theme
from careeros_personal_brand import (
    ContentProgressRepository,
    PersonalBrandDivision,
    TestimonialRepository,
)

st.set_page_config(page_title="Personal Brand", page_icon="📣", layout="wide")

inject_theme()
account = require_account()
division = PersonalBrandDivision(
    ContentProgressRepository(account.store), TestimonialRepository(account.store)
)

st.title("Personal brand")

brain = primary_brain(account.store)
if brain is None:
    st.info("Create your Career Brain first, on the Career Brain page.")
    st.stop()
if not brain.projects:
    st.info(
        "Add a project on the Career Brain page — content is generated from your real projects."
    )
    st.stop()

project_names = {project.name: project for project in brain.projects}
chosen = st.selectbox("Project", list(project_names))
project = project_names[chosen]

if st.button("Generate content from this project"):
    case_study = division.generate_case_study(brain, project)
    st.session_state[f"cs_{project.id}"] = {
        "linkedin": division.generate_linkedin_post(case_study),
        "thread": division.generate_x_thread(case_study),
        "portfolio": division.generate_portfolio_page(case_study, project),
        "blog": division.generate_blog_post(case_study),
    }

content = st.session_state.get(f"cs_{project.id}")
if content is not None:
    tab_li, tab_x, tab_portfolio, tab_blog = st.tabs(
        ["LinkedIn post", "X thread", "Portfolio page", "Blog post"]
    )
    tab_li.text_area("LinkedIn", content["linkedin"], height=220, key=f"li_{project.id}")
    tab_x.text_area("X thread", "\n\n".join(content["thread"]), height=220, key=f"x_{project.id}")
    tab_portfolio.text_area(
        "Portfolio (markdown)", content["portfolio"], height=260, key=f"pf_{project.id}"
    )
    tab_blog.text_area("Blog post", content["blog"], height=300, key=f"bl_{project.id}")
