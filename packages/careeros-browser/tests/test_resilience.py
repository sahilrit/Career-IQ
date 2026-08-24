"""Tests for the browser-resilience primitives.

These are the reusable pieces a Cloudflare-gated source needs: detecting a
challenge page, and carrying a solved clearance cookie forward with the
exact user-agent that earned it. They are pure Python — no browser binary —
so they are testable on their own and ready for the day a provider that
needs them is added.
"""

from __future__ import annotations

import time

from careeros_browser.resilience import (
    CF_CHALLENGE_MARKERS,
    CookieJar,
    PersistentCookieStore,
    is_challenge_html,
    is_challenge_status,
    retry_with_backoff,
)
from careeros_common import DocumentStore

# --- challenge detection -----------------------------------------------------


def test_a_cloudflare_interstitial_is_detected():
    html = "<html><head><title>Just a moment...</title></head><body>cf-turnstile</body></html>"
    assert is_challenge_html(html) is True


def test_each_known_marker_is_detected():
    for marker in CF_CHALLENGE_MARKERS:
        assert is_challenge_html(f"<html>{marker}</html>") is True


def test_ordinary_html_is_not_a_challenge():
    assert is_challenge_html("<html><body><h1>Jobs</h1></body></html>") is False


def test_challenge_detection_is_case_insensitive():
    assert is_challenge_html("<html>JUST A MOMENT...</html>") is True


def test_a_403_or_503_from_cloudflare_is_a_challenge():
    assert is_challenge_status(403, {"server": "cloudflare"}) is True
    assert is_challenge_status(503, {"Server": "Cloudflare"}) is True


def test_a_200_is_not_a_challenge_by_status():
    # The managed challenge returns 200 with challenge HTML; status alone is
    # not enough, which is why html detection exists alongside this.
    assert is_challenge_status(200, {"server": "cloudflare"}) is False


def test_a_403_from_a_non_cloudflare_server_is_not_flagged():
    assert is_challenge_status(403, {"server": "nginx"}) is False


# --- persistent cookie jar ---------------------------------------------------


def _store():
    return DocumentStore()


def test_a_saved_jar_can_be_loaded_back():
    with _store() as store:
        cookies = PersistentCookieStore(store)
        cookies.save(
            "naukri",
            CookieJar(
                cookies={"cf_clearance": "abc", "sessionid": "xyz"},
                user_agent="Mozilla/5.0 (X)",
            ),
        )
        loaded = cookies.load("naukri")
        assert loaded is not None
        assert loaded.cookies["cf_clearance"] == "abc"
        assert loaded.user_agent == "Mozilla/5.0 (X)"


def test_loading_an_unknown_extractor_returns_none():
    with _store() as store:
        assert PersistentCookieStore(store).load("nope") is None


def test_the_user_agent_is_stored_with_the_cookies():
    """cf_clearance is bound to the UA that earned it, so the two must never be
    separated — a reused clearance cookie with a mismatched UA is worthless."""
    with _store() as store:
        cookies = PersistentCookieStore(store)
        cookies.save("gradcracker", CookieJar(cookies={"cf_clearance": "z"}, user_agent="UA/1"))
        assert cookies.load("gradcracker").user_agent == "UA/1"


def test_each_extractor_has_its_own_jar():
    with _store() as store:
        cookies = PersistentCookieStore(store)
        cookies.save("a", CookieJar(cookies={"k": "1"}, user_agent="UA"))
        cookies.save("b", CookieJar(cookies={"k": "2"}, user_agent="UA"))
        assert cookies.load("a").cookies["k"] == "1"
        assert cookies.load("b").cookies["k"] == "2"


def test_invalidating_a_jar_removes_it():
    with _store() as store:
        cookies = PersistentCookieStore(store)
        cookies.save("naukri", CookieJar(cookies={"cf_clearance": "x"}, user_agent="UA"))
        cookies.invalidate("naukri")
        assert cookies.load("naukri") is None


def test_a_jar_reports_whether_it_carries_a_clearance_cookie():
    assert CookieJar(cookies={"cf_clearance": "x"}, user_agent="UA").has_clearance is True
    assert CookieJar(cookies={"sessionid": "x"}, user_agent="UA").has_clearance is False


def test_cookie_header_serialises_for_an_http_client():
    jar = CookieJar(cookies={"cf_clearance": "abc", "__cf_bm": "def"}, user_agent="UA")
    header = jar.cookie_header()
    assert "cf_clearance=abc" in header
    assert "__cf_bm=def" in header
    assert header.count(";") == 1


# --- retry -------------------------------------------------------------------


def test_retry_returns_the_first_success():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        return "ok"

    assert retry_with_backoff(flaky, max_attempts=3, base_delay=0) == "ok"
    assert calls["n"] == 1


def test_retry_gives_up_after_the_limit_and_reraises():
    calls = {"n": 0}

    def always_fails():
        calls["n"] += 1
        raise RuntimeError("boom")

    try:
        retry_with_backoff(always_fails, max_attempts=3, base_delay=0)
        raise AssertionError("should have re-raised")
    except RuntimeError as exc:
        assert "boom" in str(exc)
    assert calls["n"] == 3


def test_retry_recovers_on_a_later_attempt():
    calls = {"n": 0}

    def eventually_ok():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("not yet")
        return "recovered"

    assert retry_with_backoff(eventually_ok, max_attempts=3, base_delay=0) == "recovered"


def test_retry_honours_a_should_retry_predicate():
    calls = {"n": 0}

    def fails_unretryably():
        calls["n"] += 1
        raise ValueError("fatal")

    try:
        retry_with_backoff(
            fails_unretryably,
            max_attempts=5,
            base_delay=0,
            should_retry=lambda exc: not isinstance(exc, ValueError),
        )
        raise AssertionError("should have re-raised")
    except ValueError:
        pass
    # Not retried: the predicate said this error is terminal.
    assert calls["n"] == 1


def test_retry_backoff_waits_between_attempts(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", slept.append)
    calls = {"n": 0}

    def fails_twice():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("retry")
        return "ok"

    retry_with_backoff(fails_twice, max_attempts=3, base_delay=2)
    # Exponential: 2, then 4.
    assert slept == [2, 4]
