"""Discovery support and application support are reported separately.

"Nine ATSes supported" is technically true and practically misleading: an ATS
whose jobs we can read but whose forms we cannot fill is not the same feature
as one where an application reaches submission-ready.
"""

from __future__ import annotations

import json

import pytest

from careeros_ats_providers import (
    CAPABILITIES,
    ApplicationSupport,
    AtsCapability,
    WorkdayConfigError,
    application_ready_count,
    capability_for,
    capability_table,
    load_workday_config,
    workday_boards,
)


class TestTwoAxes:
    def test_every_ats_reports_both_axes(self):
        for ats_id, capability in CAPABILITIES.items():
            assert isinstance(capability.discovery, bool), ats_id
            assert isinstance(capability.application, ApplicationSupport), ats_id

    def test_discovery_only_is_a_real_state_not_a_failure(self):
        # Workday: we read its jobs fine, and its forms need an account.
        workday = capability_for("workday")
        assert workday.discovery
        assert workday.application is ApplicationSupport.DISCOVERY_ONLY
        assert not workday.application.is_usable
        assert "account" in workday.note

    def test_greenhouse_is_partial_because_of_employer_redirects(self):
        # Not a yes/no question: the integration works and many customers
        # route applications elsewhere.
        greenhouse = capability_for("greenhouse")
        assert greenhouse.application is ApplicationSupport.PARTIAL
        assert "employer choice" in greenhouse.note

    def test_an_unverified_integration_is_never_counted_as_working(self):
        # An untested integration is a claim, not a capability.
        for ats_id in ("recruitee", "personio", "bamboohr"):
            capability = capability_for(ats_id)
            assert capability.application is ApplicationSupport.UNVERIFIED
            assert not capability.application.is_usable

    def test_an_unknown_ats_is_unverified_rather_than_assumed_working(self):
        capability = capability_for("never-heard-of-it")
        assert capability.application is ApplicationSupport.UNVERIFIED
        assert capability.note

    def test_any_limitation_must_carry_a_reason(self):
        # A limitation with no reason cannot be planned around.
        with pytest.raises(ValueError, match="needs a reason"):
            AtsCapability("x", discovery=True, application=ApplicationSupport.PARTIAL)

    def test_the_headline_number_counts_application_support_not_adapters(self):
        # The number to quote instead of "nine ATSes supported".
        assert application_ready_count() < len(CAPABILITIES)
        assert application_ready_count() == sum(
            1 for c in CAPABILITIES.values() if c.application.is_usable
        )


class TestTable:
    def test_the_table_has_both_columns_and_the_notes(self):
        table = capability_table()
        assert "DISCOVERY" in table and "APPLICATION" in table
        assert "DISCOVERY_ONLY" in table
        assert "Notes:" in table

    def test_live_health_replaces_the_static_discovery_column(self):
        table = capability_table(health={"lever": "healthy", "ashby": "down"})
        assert "HEALTHY" in table
        assert "DOWN" in table
        # An ATS with no live reading is UNKNOWN, not silently "fine".
        assert "UNKNOWN" in table


class TestWorkdayConfiguration:
    def test_a_tenant_can_be_added_without_a_code_change(self, monkeypatch):
        monkeypatch.setenv(
            "CAREEROS_WORKDAY_BOARDS",
            json.dumps([{"slug": "acme", "name": "Acme", "region": "wd3", "site": "External"}]),
        )
        boards = workday_boards()
        assert [b.slug for b in boards] == ["acme"]
        assert boards[0].extra["region"] == "wd3"
        assert boards[0].extra["site"] == "External"

    def test_the_builtin_list_is_used_when_nothing_is_configured(self, monkeypatch):
        monkeypatch.delenv("CAREEROS_WORKDAY_BOARDS", raising=False)
        assert len(workday_boards()) >= 8

    def test_a_missing_site_is_rejected_at_load_time_not_at_crawl_time(self):
        # Otherwise it surfaces as a 404 four minutes into a search, which
        # reads like the company deleted its board.
        with pytest.raises(WorkdayConfigError, match="site"):
            load_workday_config(json.dumps([{"slug": "acme", "region": "wd3"}]))

    def test_a_malformed_region_says_what_a_region_looks_like(self):
        with pytest.raises(WorkdayConfigError, match="wd1"):
            load_workday_config(
                json.dumps([{"slug": "acme", "region": "europe", "site": "External"}])
            )

    def test_invalid_json_is_reported_as_invalid_json(self):
        with pytest.raises(WorkdayConfigError, match="not valid JSON"):
            load_workday_config("{oops")

    def test_a_non_array_config_explains_the_expected_shape(self):
        with pytest.raises(WorkdayConfigError, match="JSON array"):
            load_workday_config('{"slug": "acme"}')

    def test_a_bad_entry_raises_rather_than_being_silently_skipped(self):
        # Silently dropping a tenant the user deliberately configured is worse
        # than refusing to start.
        with pytest.raises(WorkdayConfigError):
            load_workday_config(
                json.dumps(
                    [
                        {"slug": "good", "region": "wd1", "site": "External"},
                        {"slug": "bad", "region": "wd1"},
                    ]
                )
            )
