"""An employer redirect is not an ATS failure.

Three of the four sampled Greenhouse employers publish through Greenhouse and
route every application to their own careers site. Reporting that as "no form
found" made a working integration look broken and sent the user hunting for a
fault that was not ours. These states exist so that stops happening.
"""

from __future__ import annotations

from careeros_autopilot import ApplicationRoute, classify_route, prepare_application
from careeros_browser import FakeBrowserSession
from careeros_job_providers import JobPosting


def posting(**kwargs) -> JobPosting:
    defaults = {
        "source_provider": "ats:greenhouse",
        "external_id": "1",
        "title": "Performance Marketing Manager",
        "company_name": "Stripe",
        "url": "https://boards.greenhouse.io/stripe/jobs/1",
    }
    return JobPosting(**{**defaults, **kwargs})


class TestClassifyRoute:
    def test_a_form_on_the_ats_host_is_ats_hosted(self):
        route = classify_route(
            posting(), "https://boards.greenhouse.io/stripe/jobs/1", form_found=True
        )
        assert route is ApplicationRoute.ATS_HOSTED

    def test_an_ats_host_with_no_form_is_unknown_not_an_employer_redirect(self):
        # We are still on the ATS; blaming the employer would be wrong.
        route = classify_route(
            posting(), "https://boards.greenhouse.io/stripe/jobs/1", form_found=False
        )
        assert route is ApplicationRoute.UNKNOWN

    def test_an_ats_posting_that_lands_off_host_with_no_form_is_an_employer_redirect(self):
        route = classify_route(posting(), "https://stripe.com/jobs/listing/1", form_found=False)
        assert route is ApplicationRoute.EXTERNAL_UNSUPPORTED

    def test_a_fillable_form_on_the_employers_own_site_is_a_supported_external_route(self):
        # Found a real form off-ATS: that is a success, not a downgrade.
        route = classify_route(posting(), "https://stripe.com/jobs/apply/1", form_found=True)
        assert route is ApplicationRoute.EXTERNAL

    def test_a_non_ats_posting_with_no_form_is_our_problem_not_the_employers(self):
        # An aggregator posting we simply could not read must NOT be reported
        # as "the employer routes applications elsewhere".
        aggregator = posting(
            source_provider="remoteok",
            url="https://remoteok.com/remote-jobs/1",
        )
        route = classify_route(aggregator, "https://someco.example/careers", form_found=False)
        assert route is ApplicationRoute.UNKNOWN

    def test_an_ats_apply_url_also_counts_as_coming_from_an_ats(self):
        # These employers publish an off-host apply URL, so the redirect has
        # already happened by the time we see the posting.
        aggregator = posting(
            source_provider="remoteok",
            url="https://remoteok.com/remote-jobs/1",
            apply_url="https://boards.greenhouse.io/acme/jobs/9",
        )
        route = classify_route(aggregator, "https://acme.example/careers", form_found=False)
        assert route is ApplicationRoute.EXTERNAL_UNSUPPORTED


class RedirectingSession(FakeBrowserSession):
    """A session that lands somewhere other than where it was sent — which is
    exactly what these employers' postings do."""

    def __init__(self, lands_at: str) -> None:
        super().__init__()
        self._lands_at = lands_at

    def goto(self, url: str) -> None:
        super().goto(self._lands_at)


class TestWhatCountsAgainstUs:
    def test_an_employer_redirect_does_not_count_against_ats_coverage(self):
        session = RedirectingSession("https://stripe.com/jobs/listing/1")
        result = prepare_application(session, posting())
        assert result.route is ApplicationRoute.EXTERNAL_UNSUPPORTED
        assert not result.is_our_problem
        # And it still tells the user what to do about it.
        assert "by hand" in result.error
        assert result.human_can_continue

    def test_the_message_names_the_site_the_application_actually_lives_on(self):
        session = RedirectingSession("https://stripe.com/jobs/listing/1")
        result = prepare_application(session, posting())
        assert "stripe.com" in result.error

    def test_staying_on_the_ats_with_no_form_is_still_our_problem(self):
        # No redirect happened, so there is nobody else to blame.
        session = FakeBrowserSession()
        result = prepare_application(session, posting())
        assert result.route is ApplicationRoute.UNKNOWN
        assert result.is_our_problem

    def test_a_genuine_detection_failure_does_count_against_us(self):
        session = FakeBrowserSession()
        result = prepare_application(
            session, posting(source_provider="remoteok", url="https://remoteok.com/jobs/1")
        )
        assert result.route is ApplicationRoute.UNKNOWN
        assert result.is_our_problem

    def test_every_failure_carries_the_url_it_ended_on(self):
        # The single most useful piece of evidence for reproducing one.
        session = FakeBrowserSession()
        result = prepare_application(session, posting())
        assert result.landed_url


class TestAntiBotWallsAreNamedNotMisdiagnosed:
    """An apply URL behind a challenge is not a missing form.

    Observed live on apply.workable.com (2026-08-31): Cloudflare Turnstile now
    says "Just a sec!" / "Verifying you are human", so the older
    "just a moment" / "verify you are human" patterns both missed and the run
    reported "no application form or apply link found on the posting page".
    That sends the user hunting for a CareerOS bug that does not exist.
    """

    def _blocked_by(self, marker: str):
        session = FakeBrowserSession()
        session.set_visible(marker)
        return prepare_application(session, posting())

    def test_the_cloudflare_challenge_iframe_is_recognised(self):
        result = self._blocked_by("iframe[src*='challenges.cloudflare.com']")
        assert "bot-protection" in result.error

    def test_the_datadome_challenge_iframe_is_recognised(self):
        result = self._blocked_by("iframe[src*='captcha-delivery.com']")
        assert "bot-protection" in result.error

    def test_the_current_cloudflare_copy_is_recognised(self):
        # "Just a sec!" — the wording that actually shipped.
        assert "bot-protection" in self._blocked_by("text=/just a (moment|sec)/i").error

    def test_the_verifying_wording_is_recognised(self):
        assert "bot-protection" in self._blocked_by("text=/verif(y|ying) you are human/i").error

    def test_a_challenge_is_never_reported_as_a_missing_form(self):
        result = self._blocked_by("iframe[src*='challenges.cloudflare.com']")
        assert "no application form" not in result.error
        assert result.human_can_continue

    def test_an_ordinary_page_is_not_flagged_as_a_challenge(self):
        session = FakeBrowserSession()
        session.set_visible("#email")
        result = prepare_application(session, posting())
        assert "bot-protection" not in (result.error or "")
