"""Tests for RemoteOK JSON entry parsing."""

from __future__ import annotations

from careeros_remoteok_provider.parser import is_job_entry, parse_job_entry


def test_legal_metadata_entry_is_not_a_job_entry(remoteok_fixture):
    assert is_job_entry(remoteok_fixture[0]) is False


def test_job_entries_are_recognized(remoteok_fixture):
    assert is_job_entry(remoteok_fixture[1]) is True
    assert is_job_entry(remoteok_fixture[2]) is True


def test_parses_core_fields(remoteok_fixture):
    posting = parse_job_entry(remoteok_fixture[1])
    assert posting.source_provider == "remoteok"
    assert posting.external_id == "1000001"
    assert posting.title == "Senior Backend Engineer"
    assert posting.company_name == "Acme Corp"
    assert posting.url == "https://remoteok.com/remote-jobs/1000001"
    assert posting.tags == ["python", "django", "postgres"]


def test_remote_is_always_true():
    posting = parse_job_entry(
        {"id": "1", "position": "Engineer", "company": "Acme", "location": "US Only"}
    )
    assert posting.remote is True


def test_parses_salary_when_present(remoteok_fixture):
    posting = parse_job_entry(remoteok_fixture[1])
    assert posting.salary.min_amount == 120000
    assert posting.salary.max_amount == 160000


def test_salary_is_none_when_not_listed(remoteok_fixture):
    posting = parse_job_entry(remoteok_fixture[2])
    assert posting.salary is None


def test_parses_posted_at_as_a_datetime(remoteok_fixture):
    posting = parse_job_entry(remoteok_fixture[1])
    assert posting.posted_at is not None
    assert posting.posted_at.year == 2026


def test_missing_date_yields_no_posted_at():
    posting = parse_job_entry({"id": "1", "position": "Engineer", "company": "Acme"})
    assert posting.posted_at is None


def test_falls_back_to_apply_url_when_url_missing():
    posting = parse_job_entry(
        {"id": "1", "position": "Engineer", "company": "Acme", "apply_url": "https://x.example"}
    )
    assert posting.url == "https://x.example"


def test_keyword_stuffed_spam_entry_is_not_a_job():
    entry = {
        "id": 99,
        "position": "barber",
        "tags": [f"tag{i}" for i in range(30)],
    }
    assert not is_job_entry(entry)


def test_normal_tag_count_is_a_job():
    entry = {"id": 100, "position": "Marketing Manager", "tags": ["marketing", "ads"]}
    assert is_job_entry(entry)
