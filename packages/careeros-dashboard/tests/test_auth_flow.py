"""Headless tests for the SaaS auth gate: landing page, signup, session
handling, tenant isolation between two real accounts, and admin access.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from careeros_auth import AuthService
from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_dashboard.data_access import open_store
from careeros_tenancy import TenantScopedDocumentStore

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "careeros_dashboard"
_TOKEN_KEY = "careeros_session_token"
PASSWORD = "Very-Secure-Password-1!"


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "data"
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(path))
    monkeypatch.delenv("CAREEROS_SINGLE_USER", raising=False)
    yield path


def sign_up(data_dir, email="ada@example.com", full_name="Ada Lovelace"):
    store = open_store(data_dir)
    try:
        return AuthService(store).sign_up(email=email, password=PASSWORD, full_name=full_name)
    finally:
        store.close()


def run_page(page, token=None):
    at = AppTest.from_file(str(_PACKAGE_ROOT / page))
    if token is not None:
        at.session_state[_TOKEN_KEY] = token
    return at.run()


def test_signed_out_home_shows_landing_with_login_and_signup(data_dir):
    at = run_page("app.py")
    assert not at.exception
    assert "CareerOS" in at.title[0].value
    assert len(at.tabs) >= 2
    # No dashboard metrics leak to signed-out visitors.
    assert not at.metric


def test_signup_form_creates_an_account_and_enters_the_app(data_dir):
    at = run_page("app.py")
    # Landing order: login (email, password), then signup (name, email, password).
    at.text_input[2].input("Ada Lovelace")
    at.text_input[3].input("ada@example.com")
    at.text_input[4].input(PASSWORD)
    at.button[1].click().run()
    assert not at.exception
    assert at.metric  # dashboard KPIs render → signed in


def test_weak_password_shows_policy_error(data_dir):
    at = run_page("app.py")
    at.text_input[2].input("Ada Lovelace")
    at.text_input[3].input("ada@example.com")
    at.text_input[4].input("short")
    at.button[1].click().run()
    assert not at.exception
    assert any("Password" in error.value for error in at.error)


def test_valid_session_token_reaches_the_dashboard(data_dir):
    _, token = sign_up(data_dir)
    at = run_page("app.py", token=token)
    assert not at.exception
    assert at.metric


def test_garbage_session_token_falls_back_to_landing(data_dir):
    at = run_page("app.py", token="not-a-real-token")
    assert not at.exception
    assert not at.metric


def test_two_accounts_are_tenant_isolated(data_dir):
    _, token_a = sign_up(data_dir, email="a@example.com", full_name="User A")
    _, token_b = sign_up(data_dir, email="b@example.com", full_name="User B")

    # User A creates a Career Brain in their workspace.
    store = open_store(data_dir)
    try:
        service = AuthService(store)
        account_a = service.validate_session(token_a)
        scoped_a = TenantScopedDocumentStore(store, account_a.workspace_id)
        CareerBrainRepository(scoped_a).save(
            CareerBrain(identity=Identity(full_name="User A", email="a@example.com"))
        )
    finally:
        store.close()

    at_a = run_page("app.py", token=token_a)
    assert "User A" in at_a.caption[0].value or any(
        "User A" in caption.value for caption in at_a.caption
    )

    at_b = run_page("app.py", token=token_b)
    assert not at_b.exception
    assert any("No Career Brain yet" in info.value for info in at_b.info)


def test_admin_page_denies_non_admins_and_admits_admins(data_dir, monkeypatch):
    _, token = sign_up(data_dir)

    monkeypatch.setenv("CAREEROS_ADMIN_EMAILS", "someone-else@example.com")
    at = run_page("pages/5_Admin.py", token=token)
    assert any("don't have access" in error.value for error in at.error)

    monkeypatch.setenv("CAREEROS_ADMIN_EMAILS", "ada@example.com")
    at = run_page("pages/5_Admin.py", token=token)
    assert not at.exception
    assert any(metric.label == "Accounts" for metric in at.metric)


def test_billing_page_shows_current_plan(data_dir):
    _, token = sign_up(data_dir)
    at = run_page("pages/3_Billing.py", token=token)
    assert not at.exception
    assert any("Current plan" in markdown.value for markdown in at.markdown)


def test_forgot_password_tab_is_present(data_dir):
    at = run_page("app.py")
    assert not at.exception
    assert len(at.tabs) >= 3


def test_reset_token_url_shows_reset_form(data_dir):
    _, _ = sign_up(data_dir)
    store = open_store(data_dir)
    try:
        reset_token = AuthService(store).request_password_reset("ada@example.com")
    finally:
        store.close()
    at = AppTest.from_file(str(_PACKAGE_ROOT / "app.py"))
    at.query_params["reset_token"] = reset_token
    at.run()
    assert not at.exception
    assert any("new password" in title.value.lower() for title in at.title)
