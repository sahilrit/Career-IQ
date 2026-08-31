"""Each adapter against a recorded payload shape from its real API."""

from __future__ import annotations

from careeros_ats_providers import BoardEntry
from careeros_ats_providers.adapters import (
    AshbyAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    SmartRecruitersAdapter,
    WorkableAdapter,
)
from careeros_ats_providers.adapters.greenhouse import build_office_map, is_work_model_only

ENTRY = BoardEntry("acme", "Acme")


class TestGreenhouse:
    def test_maps_a_posting(self):
        raw = {
            "id": 42,
            "title": "Growth Marketing Manager",
            "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/42",
            "location": {"name": "Remote - US"},
            "content": "&lt;p&gt;Own paid acquisition&lt;/p&gt;",
            "first_published": "2026-02-01T09:00:00Z",
        }
        posting = GreenhouseAdapter().to_posting(raw, ENTRY)
        assert posting.title == "Growth Marketing Manager"
        assert posting.company_name == "Acme"
        assert posting.description == "Own paid acquisition"
        assert posting.remote is True
        # A Greenhouse posting page IS the form, so apply_url must not be empty.
        assert posting.apply_url == raw["absolute_url"]

    def test_skips_a_posting_with_no_url(self):
        # A posting CareerOS cannot open is worse than no posting: it looks
        # actionable in the UI and fails at apply time.
        assert GreenhouseAdapter().to_posting({"id": 1, "title": "X"}, ENTRY) is None

    def test_office_enrichment_recovers_a_city(self):
        raw = {
            "id": 7,
            "title": "Analyst",
            "absolute_url": "https://job-boards.greenhouse.io/acme/jobs/7",
            "location": {"name": "Hybrid"},
            "_offices": ["Dublin"],
        }
        assert "Dublin" in GreenhouseAdapter().to_posting(raw, ENTRY).location


class TestWorkModelDetection:
    def test_bare_work_models_are_flagged(self):
        assert is_work_model_only("Hybrid")
        assert is_work_model_only("Distributed; Hybrid")

    def test_a_location_with_a_place_is_left_alone(self):
        # Enrichment must never rewrite a location that was already filterable.
        assert not is_work_model_only("Hybrid - London")
        assert not is_work_model_only("Remote (Canada)")

    def test_non_strings(self):
        assert not is_work_model_only(None) and not is_work_model_only(7)


class TestOfficeMap:
    def test_collects_every_office_a_job_is_listed_under(self):
        payload = {
            "offices": [
                {"name": "Dublin", "departments": [{"jobs": [{"id": 1}, {"id": 2}]}]},
                {"name": "Berlin", "departments": [{"jobs": [{"id": 1}]}]},
            ]
        }
        assert build_office_map(payload)[1] == ["Dublin", "Berlin"]

    def test_walks_nested_child_offices(self):
        payload = {
            "offices": [
                {
                    "name": "EMEA",
                    "departments": [],
                    "children": [{"name": "Oslo", "departments": [{"jobs": [{"id": 9}]}]}],
                }
            ]
        }
        assert build_office_map(payload)[9] == ["Oslo"]

    def test_malformed_payloads_are_empty_not_an_error(self):
        assert build_office_map(None) == {}
        assert build_office_map({"offices": "nope"}) == {}


class TestLever:
    def test_maps_a_posting_with_all_locations(self):
        raw = {
            "id": "abc",
            "text": "Performance Marketer",
            "hostedUrl": "https://jobs.lever.co/acme/abc",
            "categories": {
                "location": "London",
                "allLocations": ["London", "Dublin"],
                "commitment": "Full-time",
            },
            "descriptionPlain": "Run the paid programme.",
            "createdAt": 1_741_000_000_000,
        }
        posting = LeverAdapter().to_posting(raw, ENTRY)
        assert posting.location == "London; Dublin"
        assert posting.employment_type == "full_time"
        assert posting.posted_at.year == 2025
        # Lever's form lives at /apply with no crawlable link to it.
        assert posting.apply_url.endswith("/apply")


class TestAshby:
    def test_annualizes_monthly_compensation(self):
        raw = {
            "id": "x1",
            "title": "Data Analyst",
            "jobUrl": "https://jobs.ashbyhq.com/acme/x1",
            "location": "Remote",
            "isRemote": True,
            "compensation": {
                "minValue": 8000,
                "maxValue": 10000,
                "currency": "eur",
                "interval": "1 MONTH",
            },
            "descriptionPlain": "Analytics.",
        }
        posting = AshbyAdapter().to_posting(raw, ENTRY)
        assert posting.salary.min_amount == 96_000
        assert posting.salary.currency == "EUR"
        assert posting.apply_url.endswith("/application")

    def test_secondary_locations_are_kept(self):
        raw = {
            "id": "x2",
            "title": "PM",
            "jobUrl": "https://jobs.ashbyhq.com/acme/x2",
            "location": "New York",
            "secondaryLocations": [{"location": "Austin"}],
        }
        assert AshbyAdapter().to_posting(raw, ENTRY).location == "New York; Austin"


class TestSmartRecruiters:
    def test_assembles_the_description_from_sections(self):
        from careeros_ats_providers.adapters.smartrecruiters import extract_description

        detail = {
            "jobAd": {
                "sections": {
                    "jobDescription": {"text": "<p>Do the work</p>"},
                    "qualifications": {"text": "<p>Five years</p>"},
                }
            }
        }
        assert extract_description(detail) == "Do the work\n\nFive years"

    def test_missing_sections_are_empty(self):
        from careeros_ats_providers.adapters.smartrecruiters import extract_description

        assert extract_description({}) == "" and extract_description(None) == ""

    def test_maps_a_posting(self):
        raw = {
            "id": "999",
            "name": "Brand Manager",
            "company": {"name": "Acme Global"},
            "location": {"city": "Berlin", "country": "de", "remote": False},
            "releasedDate": "2026-01-15T00:00:00.000Z",
        }
        posting = SmartRecruitersAdapter().to_posting(raw, ENTRY)
        assert posting.company_name == "Acme Global"
        assert posting.location == "Berlin; de"


class TestWorkable:
    def test_maps_a_posting(self):
        raw = {
            "shortcode": "AB12",
            "title": "Paid Social Lead",
            "url": "https://apply.workable.com/acme/j/AB12",
            "city": "Athens",
            "country": "Greece",
            "telecommuting": True,
            "description": "<p>Scale spend</p>",
            "published_on": "2026-02-20",
        }
        posting = WorkableAdapter().to_posting(raw, ENTRY)
        assert posting.remote is True
        assert posting.description == "Scale spend"
        assert posting.external_id == "AB12"
