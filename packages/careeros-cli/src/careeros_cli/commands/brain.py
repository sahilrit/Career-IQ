"""`careeros brain ...` commands."""

from __future__ import annotations

import argparse
import sys

from careeros_career_brain import CareerBrain, Identity
from careeros_cli.context import CLIContext, build_context
from careeros_memory import applications_by_status


def create_brain(
    context: CLIContext, *, full_name: str, email: str, headline: str = ""
) -> CareerBrain:
    brain = CareerBrain(identity=Identity(full_name=full_name, email=email, headline=headline))
    context.repository.save(brain)
    return brain


def format_brain_summary(brain: CareerBrain) -> str:
    lines = [f"{brain.identity.full_name} <{brain.identity.email}>"]
    if brain.identity.headline:
        lines.append(brain.identity.headline)
    lines.append(f"Skills: {len(brain.skills)}")
    lines.append(f"Experiences: {len(brain.experiences)}")
    lines.append("Applications by status:")
    for status, count in applications_by_status(brain).items():
        if count:
            lines.append(f"  {status}: {count}")
    return "\n".join(lines)


def cmd_create(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    brain = create_brain(
        context, full_name=args.full_name, email=args.email, headline=args.headline
    )
    print(brain.identity.id)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    brain = context.repository.load_or_none(args.identity_id)
    if brain is None:
        print(f"No Career Brain found with id {args.identity_id!r}", file=sys.stderr)
        return 1
    print(format_brain_summary(brain))
    return 0
