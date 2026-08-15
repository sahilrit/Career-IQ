"""Tests for check_browser_health, via an injected fake session_factory
(no real browser launch)."""

from __future__ import annotations

from contextlib import contextmanager

from careeros_browser import BrowserHealthStatus, FakeBrowserSession, check_browser_health


@contextmanager
def _working_session_factory():
    session = FakeBrowserSession()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def _broken_session_factory():
    raise RuntimeError("could not launch browser")
    yield  # pragma: no cover - unreachable, keeps this a generator


def test_healthy_when_session_launches_and_navigates():
    health = check_browser_health(session_factory=_working_session_factory)
    assert health.status == BrowserHealthStatus.HEALTHY


def test_down_when_session_factory_raises():
    health = check_browser_health(session_factory=_broken_session_factory)
    assert health.status == BrowserHealthStatus.DOWN
    assert "could not launch browser" in health.detail
