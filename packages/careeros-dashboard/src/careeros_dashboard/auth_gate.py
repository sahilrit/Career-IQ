"""The dashboard's front door: every page calls ``require_account()``
first. Signed out, it renders the marketing landing page with login /
signup and stops the script; signed in, it returns an ``AccountContext``
whose ``store`` is tenant-scoped — so page code written against a plain
DocumentStore is customer-isolated without further changes.

Two deployment modes, chosen by environment:

- SaaS (default): full auth; every account gets its own workspace.
- Single-user (``CAREEROS_SINGLE_USER=1``): no login, unscoped store —
  the original local/self-hosted behavior for a personal install.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st

from careeros_auth import (
    AccountLockedError,
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PasswordPolicyError,
)
from careeros_billing import PLANS, PlanTier
from careeros_common import DocumentStore
from careeros_dashboard.runtime import get_store
from careeros_tenancy import Role, TenantScopedDocumentStore, User

_TOKEN_KEY = "careeros_session_token"

PASSWORD_REQUIREMENTS = "At least 12 characters, with an uppercase letter, a digit, and a symbol."


@dataclass(frozen=True)
class AccountContext:
    user: User | None
    workspace_id: str | None
    role: Role | None
    store: DocumentStore | TenantScopedDocumentStore
    raw_store: DocumentStore
    is_admin: bool


def single_user_mode() -> bool:
    return os.environ.get("CAREEROS_SINGLE_USER", "") == "1"


def admin_emails() -> frozenset[str]:
    raw = os.environ.get("CAREEROS_ADMIN_EMAILS", "")
    return frozenset(email.strip().lower() for email in raw.split(",") if email.strip())


def get_auth_service() -> AuthService:
    return AuthService(get_store())


def require_account() -> AccountContext:
    """Return the signed-in account, or render the landing page and stop."""
    raw_store = get_store()

    if single_user_mode():
        return AccountContext(
            user=None,
            workspace_id=None,
            role=None,
            store=raw_store,
            raw_store=raw_store,
            is_admin=True,
        )

    auth = get_auth_service()

    reset_token = st.query_params.get("reset_token")
    if reset_token:
        _render_password_reset_form(auth, reset_token)
        st.stop()
        raise RuntimeError("unreachable")

    token = st.session_state.get(_TOKEN_KEY)
    account = auth.validate_session(token) if token else None
    if account is None:
        if token:
            del st.session_state[_TOKEN_KEY]
        _render_landing(auth)
        st.stop()
        raise RuntimeError("unreachable")  # st.stop() never returns

    _render_sidebar_account(auth, account.user, token)
    return AccountContext(
        user=account.user,
        workspace_id=account.workspace_id,
        role=account.role,
        store=TenantScopedDocumentStore(raw_store, account.workspace_id),
        raw_store=raw_store,
        is_admin=account.user.email in admin_emails(),
    )


def _render_sidebar_account(auth: AuthService, user: User, token: str) -> None:
    with st.sidebar:
        st.caption(f"Signed in as **{user.full_name or user.email}**")
        if st.button("Sign out", width="stretch"):
            auth.log_out(token)
            del st.session_state[_TOKEN_KEY]
            st.rerun()


# -- landing page -----------------------------------------------------------


def _render_landing(auth: AuthService) -> None:
    st.title("CareerOS")
    st.subheader("Your career, run like a company.")
    st.write(
        "CareerOS is an AI career operating system: build a **Career Brain** "
        "from your real experience, discover matching jobs and freelance "
        "clients automatically, generate tailored resumes, cover letters, and "
        "pitches in one click, and track every application, interview, offer, "
        "and invoice in one place."
    )

    feature_cols = st.columns(3)
    features = [
        ("🧠 Career Brain", "One authoritative profile powering every resume and pitch."),
        ("🎯 Opportunity discovery", "Jobs and freelance clients found and scored for you."),
        ("📄 One-click applications", "Tailored resume + cover letter per posting."),
        ("📅 Pipeline tracking", "Applications, interviews, offers, and follow-ups."),
        ("💼 Freelance CRM", "Prospects, audits, proposals, clients, and income."),
        ("🔒 Private by design", "Your workspace is isolated; export or delete anytime."),
    ]
    for index, (title, description) in enumerate(features):
        with feature_cols[index % 3]:
            st.markdown(f"**{title}**\n\n{description}")

    st.divider()
    st.subheader("Pricing")
    price_cols = st.columns(len(PLANS))
    for column, tier in zip(price_cols, PlanTier, strict=True):
        plan = PLANS[tier]
        with column:
            st.markdown(f"### {plan.name}")
            st.markdown(f"**${plan.monthly_price_usd:,.0f}/mo**")
            for feature in plan.features:
                st.markdown(f"- {feature.replace('_', ' ').capitalize()}")

    st.divider()
    login_tab, signup_tab, reset_tab = st.tabs(["Log in", "Create account", "Forgot password"])
    with login_tab:
        _render_login(auth)
    with signup_tab:
        _render_signup(auth)
    with reset_tab:
        _render_password_reset_request(auth)


def _render_login(auth: AuthService) -> None:
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log in", width="stretch"):
            try:
                st.session_state[_TOKEN_KEY] = auth.log_in(email=email, password=password)
                st.rerun()
            except AccountLockedError:
                st.error("Too many failed attempts — this account is locked for 15 minutes.")
            except InvalidCredentialsError:
                st.error("Email or password is incorrect.")


def _render_password_reset_form(auth: AuthService, reset_token: str) -> None:
    st.title("Set a new password")
    with st.form("reset_password"):
        new_password = st.text_input("New password", type="password", help=PASSWORD_REQUIREMENTS)
        st.caption(PASSWORD_REQUIREMENTS)
        if st.form_submit_button("Reset password", width="stretch"):
            try:
                auth.reset_password(reset_token, new_password)
                st.query_params.clear()
                st.success("Password reset. Log in with your new password.")
            except PasswordPolicyError as error:
                st.error("Password " + "; ".join(error.violations) + ".")
            except InvalidCredentialsError:
                st.error("This reset link is invalid or has expired — request a new one.")


def _render_password_reset_request(auth: AuthService) -> None:
    from careeros_dashboard.email_sender import send_email, smtp_configured

    st.caption("Enter your email and we'll send a reset link (valid for 1 hour).")
    with st.form("reset_request"):
        email = st.text_input("Email", key="reset_email")
        if st.form_submit_button("Send reset link", width="stretch"):
            token = auth.request_password_reset(email)
            if token and not smtp_configured():
                # Self-serve / single-node install with no mail server: show
                # the link directly so the user is never locked out.
                st.info("Use this one-time reset link (no email server configured):")
                st.code(f"?reset_token={token}")
            elif token:
                send_email(
                    to=email.strip(),
                    subject="Reset your CareerOS password",
                    body=(
                        "Open this link to reset your password (valid 1 hour):\n\n"
                        f"?reset_token={token}\n\nIf you didn't request this, ignore this email."
                    ),
                )
            # Same message regardless, so we never reveal which emails exist.
            st.success("If that email has an account, a reset link is on its way.")


def _render_signup(auth: AuthService) -> None:
    with st.form("signup"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input(
            "Password", type="password", key="signup_password", help=PASSWORD_REQUIREMENTS
        )
        st.caption(PASSWORD_REQUIREMENTS)
        if st.form_submit_button("Create account", width="stretch"):
            if not full_name.strip() or not email.strip():
                st.error("Name and email are required.")
            else:
                try:
                    _, token = auth.sign_up(email=email, password=password, full_name=full_name)
                    st.session_state[_TOKEN_KEY] = token
                    st.rerun()
                except EmailAlreadyRegisteredError:
                    st.error("That email already has an account — log in instead.")
                except PasswordPolicyError as error:
                    st.error("Password " + "; ".join(error.violations) + ".")
