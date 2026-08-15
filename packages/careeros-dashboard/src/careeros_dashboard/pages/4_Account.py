"""Account page: profile, password change, data export (portability),
and account deletion."""

from __future__ import annotations

import json

import streamlit as st

from careeros_auth import InvalidCredentialsError, PasswordPolicyError
from careeros_dashboard.auth_gate import (
    PASSWORD_REQUIREMENTS,
    get_auth_service,
    require_account,
    single_user_mode,
)
from careeros_dashboard.data_access import primary_brain
from careeros_dashboard.theme import inject_theme

st.set_page_config(page_title="Account", page_icon="👤", layout="wide")

inject_theme()
account = require_account()

st.title("Account")

if single_user_mode():
    st.info("Single-user install — there are no accounts to manage.")
    st.stop()

st.markdown(f"**Name:** {account.user.full_name}")
st.markdown(f"**Email:** {account.user.email}")
st.markdown(f"**Role:** {account.role.value}")
st.caption(f"Member since {account.user.created_at:%B %d, %Y}")

st.divider()
st.subheader("Change password")
with st.form("change_password"):
    current_password = st.text_input("Current password", type="password")
    new_password = st.text_input("New password", type="password", help=PASSWORD_REQUIREMENTS)
    if st.form_submit_button("Change password"):
        try:
            get_auth_service().change_password(
                account.user.id,
                current_password=current_password,
                new_password=new_password,
            )
            st.success("Password changed. You've been signed out everywhere — log in again.")
        except InvalidCredentialsError:
            st.error("Current password is incorrect.")
        except PasswordPolicyError as error:
            st.error("New password " + "; ".join(error.violations) + ".")

st.divider()
st.subheader("Export your data")
brain = primary_brain(account.store)
if brain is None:
    st.caption("Nothing to export yet — your Career Brain is empty.")
else:
    st.download_button(
        "Download my data (JSON)",
        json.dumps(brain.model_dump(mode="json"), indent=2),
        file_name="careeros-export.json",
        mime="application/json",
    )

st.divider()
st.subheader("Danger zone")
with st.expander("Delete my account"):
    st.warning(
        "This permanently deletes your account, workspace access, and sessions. "
        "Your Career Brain data is removed from the active product."
    )
    confirmation = st.text_input('Type "DELETE" to confirm')
    if st.button("Delete my account", type="primary", disabled=confirmation != "DELETE"):
        get_auth_service().delete_account(account.user.id)
        st.session_state.clear()
        st.rerun()
