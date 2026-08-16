"""Network page: a lightweight CRM for the people in your career and
freelance pipeline — recruiters, founders, hiring managers, clients."""

from __future__ import annotations

import streamlit as st

from careeros_crm import (
    Contact,
    ContactRepository,
    ContactRole,
    RelationshipCRM,
    TimelineRepository,
)
from careeros_dashboard.auth_gate import require_account
from careeros_dashboard.theme import badge, inject_theme

st.set_page_config(page_title="Network", page_icon="🤝", layout="wide")

inject_theme()
account = require_account()
crm = RelationshipCRM(ContactRepository(account.store), TimelineRepository(account.store))

st.title("Network")

with st.expander("Add a contact", expanded=not crm.list_contacts()), st.form("add_contact"):
    name = st.text_input("Name")
    role = st.selectbox("Role", [r.value for r in ContactRole])
    organization = st.text_input("Organization")
    email = st.text_input("Email (optional)")
    if st.form_submit_button("Add contact") and name:
        crm.add_contact(
            Contact(
                name=name,
                role=ContactRole(role),
                organization_name=organization,
                email=email or None,
            )
        )
        st.rerun()

contacts = crm.list_contacts()
if not contacts:
    st.info("No contacts yet — add one above.")
else:
    st.subheader(f"{len(contacts)} contacts")
    for contact in contacts:
        stage = crm.timeline_for(contact.id).current_stage
        stage_label = stage.value.replace("_", " ") if stage else "new"
        org = f" · {contact.organization_name}" if contact.organization_name else ""
        st.markdown(
            f"{badge(contact.role.value.replace('_', ' '), 'blue')} **{contact.name}**{org} "
            f"— _{stage_label}_",
            unsafe_allow_html=True,
        )
