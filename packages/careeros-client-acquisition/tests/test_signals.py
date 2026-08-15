"""Tests for WebsiteSignalDetector."""

from __future__ import annotations

from careeros_client_acquisition import Company, SignalType, WebsiteSignalDetector


def _make_clean_page(fake_session):
    fake_session.set_query_all_results(
        "meta[name='description']", [{"content": "A useful description"}]
    )
    fake_session.set_visible(".testimonial")
    fake_session.set_visible("#chat-widget")
    fake_session.set_visible("body", text="x" * 250)


def test_clean_page_has_no_signals(fake_session, company):
    _make_clean_page(fake_session)
    detector = WebsiteSignalDetector(fake_session)
    assert detector.detect(company) == []


def test_http_site_is_flagged(fake_session):
    _make_clean_page(fake_session)
    company = Company(name="Insecure Co", website="http://insecure.example.com")
    detector = WebsiteSignalDetector(fake_session)
    signal_types = [s.signal_type for s in detector.detect(company)]
    assert SignalType.NO_HTTPS in signal_types


def test_missing_meta_description_is_flagged(fake_session, company):
    fake_session.set_visible(".testimonial")
    fake_session.set_visible("#chat-widget")
    fake_session.set_visible("body", text="x" * 250)
    detector = WebsiteSignalDetector(fake_session)
    signal_types = [s.signal_type for s in detector.detect(company)]
    assert SignalType.MISSING_META_DESCRIPTION in signal_types


def test_no_testimonials_is_flagged(fake_session, company):
    fake_session.set_query_all_results(
        "meta[name='description']", [{"content": "A useful description"}]
    )
    fake_session.set_visible("#chat-widget")
    fake_session.set_visible("body", text="x" * 250)
    detector = WebsiteSignalDetector(fake_session)
    signal_types = [s.signal_type for s in detector.detect(company)]
    assert SignalType.NO_TESTIMONIALS in signal_types


def test_no_live_chat_is_flagged(fake_session, company):
    fake_session.set_query_all_results(
        "meta[name='description']", [{"content": "A useful description"}]
    )
    fake_session.set_visible(".testimonial")
    fake_session.set_visible("body", text="x" * 250)
    detector = WebsiteSignalDetector(fake_session)
    signal_types = [s.signal_type for s in detector.detect(company)]
    assert SignalType.NO_LIVE_CHAT in signal_types


def test_thin_homepage_content_is_flagged(fake_session, company):
    fake_session.set_query_all_results(
        "meta[name='description']", [{"content": "A useful description"}]
    )
    fake_session.set_visible(".testimonial")
    fake_session.set_visible("#chat-widget")
    fake_session.set_visible("body", text="short")
    detector = WebsiteSignalDetector(fake_session)
    signal_types = [s.signal_type for s in detector.detect(company)]
    assert SignalType.THIN_HOMEPAGE_CONTENT in signal_types
