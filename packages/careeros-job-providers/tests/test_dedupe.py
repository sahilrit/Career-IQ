"""Tests for deduplicate().

Two kinds of duplicate, and only one of them used to be handled: the same
posting twice from one provider, and the same JOB reached from an aggregator
and from the ATS that hosts it. The second is the one a user actually sees.
"""

from __future__ import annotations

from careeros_job_providers import deduplicate
from careeros_job_providers.dedupe import identity_key, normalize_title, normalize_url


def test_keeps_first_occurrence_of_duplicate_key(posting_factory):
    first = posting_factory(source_provider="remoteok", external_id="1", title="First seen")
    duplicate = posting_factory(source_provider="remoteok", external_id="1", title="Duplicate")
    result = deduplicate([first, duplicate])
    assert len(result) == 1
    assert result[0].title == "First seen"


def test_different_providers_with_different_jobs_are_both_kept(posting_factory):
    # External ids are provider-scoped, so a shared id means nothing. These are
    # genuinely different roles and both must survive.
    a = posting_factory(
        source_provider="remoteok",
        external_id="1",
        title="Backend Engineer",
        url="https://remoteok.com/jobs/1",
    )
    b = posting_factory(
        source_provider="wellfound",
        external_id="1",
        title="Product Designer",
        url="https://wellfound.com/jobs/9",
    )
    assert len(deduplicate([a, b])) == 2


def test_empty_list_returns_empty_list():
    assert deduplicate([]) == []


class TestCrossProviderDuplicates:
    def test_the_same_job_from_an_aggregator_and_its_ats_is_one_row(self, posting_factory):
        # The duplicate that actually shows up in daily use. No shared id:
        # Himalayas calls it h-8891, Greenhouse calls it 4001209002.
        aggregator = posting_factory(
            source_provider="himalayas",
            external_id="h-8891",
            title="Performance Marketing Manager",
            company_name="Acme",
            url="https://boards.greenhouse.io/acme/jobs/4001209002?utm_source=himalayas",
            location="London, UK",
        )
        ats = posting_factory(
            source_provider="ats:greenhouse",
            external_id="4001209002",
            title="Performance Marketing Manager",
            company_name="Acme",
            url="https://boards.greenhouse.io/acme/jobs/4001209002",
            location="London, UK",
        )
        result = deduplicate([aggregator, ats])
        assert len(result) == 1

    def test_the_ats_copy_wins_because_it_can_actually_be_applied_to(self, posting_factory):
        aggregator = posting_factory(
            source_provider="himalayas",
            external_id="h-1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://himalayas.app/jobs/1",
            location="Remote",
        )
        ats = posting_factory(
            source_provider="ats:lever",
            external_id="lv-1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://jobs.lever.co/acme/1",
            location="Remote",
        )
        assert deduplicate([aggregator, ats])[0].source_provider == "ats:lever"

    def test_the_copy_with_a_description_wins_between_two_aggregators(self, posting_factory):
        thin = posting_factory(
            source_provider="a",
            external_id="1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://a.test/1",
            location="Remote",
        )
        rich = posting_factory(
            source_provider="b",
            external_id="2",
            company_name="Acme",
            title="Growth Marketer",
            url="https://b.test/2",
            location="Remote",
            description="Own paid acquisition end to end.",
        )
        assert deduplicate([thin, rich])[0].description

    def test_tracking_parameters_do_not_make_two_copies_look_different(self, posting_factory):
        clean = posting_factory(
            source_provider="a", external_id="1", url="https://jobs.lever.co/acme/1"
        )
        tagged = posting_factory(
            source_provider="b",
            external_id="2",
            url="https://jobs.lever.co/acme/1?utm_source=x&ref=y",
        )
        assert len(deduplicate([clean, tagged])) == 1

    def test_ordering_is_preserved_when_a_later_copy_replaces_an_earlier_one(self, posting_factory):
        first = posting_factory(
            source_provider="agg",
            external_id="1",
            title="Zeta",
            url="https://a.test/1",
            company_name="Acme",
            location="Remote",
        )
        other = posting_factory(
            source_provider="agg", external_id="2", title="Alpha", url="https://a.test/2"
        )
        better = posting_factory(
            source_provider="ats:lever",
            external_id="3",
            title="Zeta",
            url="https://jobs.lever.co/acme/3",
            company_name="Acme",
            location="Remote",
        )
        titles = [p.title for p in deduplicate([first, other, better])]
        assert titles == ["Zeta", "Alpha"]


class TestItDoesNotOverMerge:
    """A wrong merge silently HIDES a real job, which is worse than a duplicate."""

    def test_two_roles_at_the_same_company_in_different_cities_are_both_kept(self, posting_factory):
        london = posting_factory(
            source_provider="a",
            external_id="1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://a.test/1",
            location="London, UK",
        )
        berlin = posting_factory(
            source_provider="a",
            external_id="2",
            company_name="Acme",
            title="Growth Marketer",
            url="https://a.test/2",
            location="Berlin, Germany",
        )
        assert len(deduplicate([london, berlin])) == 2

    def test_different_titles_at_the_same_company_are_both_kept(self, posting_factory):
        a = posting_factory(
            source_provider="a",
            external_id="1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://a.test/1",
            location="Remote",
        )
        b = posting_factory(
            source_provider="a",
            external_id="2",
            company_name="Acme",
            title="Growth Engineer",
            url="https://a.test/2",
            location="Remote",
        )
        assert len(deduplicate([a, b])) == 2

    def test_postings_missing_a_location_are_never_merged_on_identity(self, posting_factory):
        # "" == "" would collapse unrelated rows, so a partial key never merges.
        a = posting_factory(
            source_provider="a",
            external_id="1",
            company_name="Acme",
            title="Growth Marketer",
            url="https://a.test/1",
        )
        b = posting_factory(
            source_provider="b",
            external_id="2",
            company_name="Acme",
            title="Growth Marketer",
            url="https://b.test/2",
        )
        assert len(deduplicate([a, b])) == 2

    def test_cross_provider_merging_can_be_switched_off(self, posting_factory):
        a = posting_factory(source_provider="a", external_id="1", url="https://x.test/1")
        b = posting_factory(source_provider="b", external_id="2", url="https://x.test/1")
        assert len(deduplicate([a, b], cross_provider=False)) == 2


class TestNormalisation:
    def test_a_remote_decoration_does_not_change_which_job_it_is(self):
        assert normalize_title("Growth Marketer (Remote)") == normalize_title("Growth Marketer")

    def test_case_and_punctuation_are_ignored(self):
        assert normalize_title("Senior  Growth-Marketer") == "senior growth marketer"

    def test_url_normalisation_strips_scheme_www_query_and_slash(self):
        normalized = normalize_url("https://www.Jobs.Lever.co/acme/1/?utm=x#top")
        assert normalized == "jobs.lever.co/acme/1"

    def test_a_remote_posting_with_no_location_still_has_an_identity(self, posting_factory):
        remote = posting_factory(
            source_provider="a",
            external_id="1",
            company_name="Acme",
            title="Growth Marketer",
            remote=True,
        )
        assert identity_key(remote) == ("acme", "growth marketer", "remote")
