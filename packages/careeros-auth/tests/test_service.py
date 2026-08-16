"""Tests for AuthService: signup provisioning, login, lockout, sessions,
expiry, and password changes — all with an injected clock."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from careeros_auth import (
    AccountLockedError,
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PasswordPolicyError,
)
from careeros_billing import SubscriptionRepository
from careeros_billing.plan import PlanTier
from careeros_common import DocumentStore
from careeros_tenancy import Role, TenancyRepository

PASSWORD = "Very-Secure-Password-1!"


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


class Clock:
    def __init__(self) -> None:
        self.current = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def service(store, clock):
    return AuthService(store, now=clock)


def sign_up(service, email="ada@example.com"):
    return service.sign_up(email=email, password=PASSWORD, full_name="Ada Lovelace")


def test_sign_up_provisions_user_workspace_membership_and_free_subscription(service, store):
    user, token = sign_up(service)

    tenancy = TenancyRepository(store)
    assert tenancy.find_user_by_email("ada@example.com") is not None
    memberships = tenancy.workspaces_for_user(user.id)
    assert len(memberships) == 1
    assert memberships[0].role == Role.OWNER

    subscription = SubscriptionRepository(store).load_or_none(memberships[0].workspace_id)
    assert subscription is not None
    assert subscription.plan_tier == PlanTier.FREE

    account = service.validate_session(token)
    assert account is not None
    assert account.user.id == user.id
    assert account.workspace_id == memberships[0].workspace_id


def test_sign_up_normalizes_email_case(service):
    sign_up(service, email="  Ada@Example.COM ")
    assert service.log_in(email="ada@example.com", password=PASSWORD)


def test_duplicate_email_is_rejected(service):
    sign_up(service)
    with pytest.raises(EmailAlreadyRegisteredError):
        sign_up(service)


def test_weak_password_is_rejected_with_violations(service):
    with pytest.raises(PasswordPolicyError) as excinfo:
        service.sign_up(email="weak@example.com", password="short", full_name="Weak")
    assert excinfo.value.violations


def test_log_in_returns_a_valid_session(service):
    user, _ = sign_up(service)
    token = service.log_in(email="ada@example.com", password=PASSWORD)
    account = service.validate_session(token)
    assert account is not None
    assert account.user.id == user.id


def test_wrong_password_and_unknown_email_raise_the_same_error(service):
    sign_up(service)
    with pytest.raises(InvalidCredentialsError):
        service.log_in(email="ada@example.com", password="Wrong-Password-1!")
    with pytest.raises(InvalidCredentialsError):
        service.log_in(email="nobody@example.com", password=PASSWORD)


def test_five_failures_lock_the_account_and_time_unlocks_it(service, clock):
    sign_up(service)
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            service.log_in(email="ada@example.com", password="Wrong-Password-1!")
    with pytest.raises(AccountLockedError):
        service.log_in(email="ada@example.com", password=PASSWORD)

    clock.advance(timedelta(minutes=16))
    assert service.log_in(email="ada@example.com", password=PASSWORD)


def test_sessions_expire(service, clock):
    _, token = sign_up(service)
    clock.advance(timedelta(days=8))
    assert service.validate_session(token) is None


def test_log_out_invalidates_the_session(service):
    _, token = sign_up(service)
    service.log_out(token)
    assert service.validate_session(token) is None


def test_garbage_token_is_rejected(service):
    assert service.validate_session("not-a-real-token") is None


def test_change_password_requires_current_and_revokes_sessions(service):
    user, token = sign_up(service)
    with pytest.raises(InvalidCredentialsError):
        service.change_password(
            user.id, current_password="Wrong-1!aaaaaa", new_password="New-Password-22!"
        )
    service.change_password(user.id, current_password=PASSWORD, new_password="New-Password-22!")
    assert service.validate_session(token) is None
    assert service.log_in(email="ada@example.com", password="New-Password-22!")


def test_delete_account_removes_identity_and_sessions(service, store):
    user, token = sign_up(service)
    service.delete_account(user.id)
    assert service.validate_session(token) is None
    assert TenancyRepository(store).find_user_by_email("ada@example.com") is None
    with pytest.raises(InvalidCredentialsError):
        service.log_in(email="ada@example.com", password=PASSWORD)


def test_password_reset_flow_sets_new_password(service, clock):
    sign_up(service)
    token = service.request_password_reset("ada@example.com")
    assert token
    service.reset_password(token, "Reset-Password-99!")
    assert service.log_in(email="ada@example.com", password="Reset-Password-99!")
    with pytest.raises(InvalidCredentialsError):
        service.log_in(email="ada@example.com", password=PASSWORD)


def test_reset_token_is_single_use(service):
    sign_up(service)
    token = service.request_password_reset("ada@example.com")
    service.reset_password(token, "Reset-Password-99!")
    with pytest.raises(InvalidCredentialsError):
        service.reset_password(token, "Another-Password-11!")


def test_reset_token_expires(service, clock):
    sign_up(service)
    token = service.request_password_reset("ada@example.com")
    clock.advance(timedelta(hours=2))
    with pytest.raises(InvalidCredentialsError):
        service.reset_password(token, "Reset-Password-99!")


def test_request_reset_for_unknown_email_returns_none(service):
    assert service.request_password_reset("nobody@example.com") is None


def test_reset_with_garbage_token_is_rejected(service):
    sign_up(service)
    with pytest.raises(InvalidCredentialsError):
        service.reset_password("not-a-real-token", "Reset-Password-99!")


def test_reset_revokes_existing_sessions(service):
    _, token = sign_up(service)
    reset_token = service.request_password_reset("ada@example.com")
    service.reset_password(reset_token, "Reset-Password-99!")
    assert service.validate_session(token) is None
