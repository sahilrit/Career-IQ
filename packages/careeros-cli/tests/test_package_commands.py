"""Tests for `careeros generate-package` command logic."""

from __future__ import annotations

from careeros_career_brain import CareerBrain, Identity
from careeros_cli.commands.package import find_posting_by_url, write_package


def test_find_posting_by_url_returns_the_matching_posting(context):
    posting = find_posting_by_url(context, "https://example.com/jobs/1")
    assert posting is not None
    assert posting.title == "Backend Engineer"


def test_find_posting_by_url_returns_none_when_no_match(context):
    assert find_posting_by_url(context, "https://example.com/does-not-exist") is None


def test_write_package_creates_every_expected_file(tmp_path, context):
    from careeros_application_engine import build_application_package

    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    posting = find_posting_by_url(context, "https://example.com/jobs/1")
    package = build_application_package(brain, posting)

    out_dir = tmp_path / "out"
    write_package(package, out_dir)

    assert (out_dir / "resume.md").read_text() == package.resume_markdown
    assert (out_dir / "resume.txt").read_text() == package.resume_text
    assert (out_dir / "resume.html").read_text() == package.resume_html
    assert (out_dir / "cover_letter.txt").read_text() == package.cover_letter
