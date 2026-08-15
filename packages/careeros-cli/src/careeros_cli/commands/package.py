"""`careeros generate-package` command: build application materials for a
job URL from currently open postings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from careeros_application_engine import ApplicationPackage, build_application_package
from careeros_cli.context import CLIContext, build_context
from careeros_job_providers import JobPosting, JobSearchQuery


def find_posting_by_url(context: CLIContext, job_url: str) -> JobPosting | None:
    result = context.provider_registry.search_all(JobSearchQuery(limit=200))
    return next((posting for posting in result.postings if posting.url == job_url), None)


def write_package(package: ApplicationPackage, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "resume.md").write_text(package.resume_markdown)
    (out_dir / "resume.txt").write_text(package.resume_text)
    (out_dir / "resume.html").write_text(package.resume_html)
    (out_dir / "cover_letter.txt").write_text(package.cover_letter)


def cmd_generate_package(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    brain = context.repository.load_or_none(args.identity_id)
    if brain is None:
        print(f"No Career Brain found with id {args.identity_id!r}", file=sys.stderr)
        return 1

    posting = find_posting_by_url(context, args.job_url)
    if posting is None:
        print(f"No open posting found with url {args.job_url!r}", file=sys.stderr)
        return 1

    package = build_application_package(brain, posting)
    if args.out_dir:
        write_package(package, Path(args.out_dir))
        print(f"Wrote application package to {args.out_dir}")
    else:
        print(package.resume_text)
        print("\n---\n")
        print(package.cover_letter)
    return 0
