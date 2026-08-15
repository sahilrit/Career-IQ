"""CareerOS CLI entry point.

Global options (like ``--data-dir``) go before the subcommand name, e.g.
``careeros --data-dir ./mydata brain create --full-name ... --email ...``.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from careeros_cli.commands.applications import cmd_list
from careeros_cli.commands.brain import cmd_create, cmd_show
from careeros_cli.commands.package import cmd_generate_package
from careeros_cli.commands.search import cmd_search

DEFAULT_DATA_DIR = ".careeros/data"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="careeros", description="CareerOS command-line interface")
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Local data directory (default: %(default)s)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    brain_parser = subparsers.add_parser("brain", help="Manage Career Brains")
    brain_subparsers = brain_parser.add_subparsers(dest="brain_command", required=True)

    create_parser = brain_subparsers.add_parser("create", help="Create a new Career Brain")
    create_parser.add_argument("--full-name", required=True)
    create_parser.add_argument("--email", required=True)
    create_parser.add_argument("--headline", default="")
    create_parser.set_defaults(func=cmd_create)

    show_parser = brain_subparsers.add_parser("show", help="Show a Career Brain summary")
    show_parser.add_argument("identity_id")
    show_parser.set_defaults(func=cmd_show)

    search_parser = subparsers.add_parser(
        "search", help="Run a job discovery + qualification cycle"
    )
    search_parser.add_argument("identity_id")
    search_parser.add_argument("--keywords", nargs="*", default=[])
    search_parser.add_argument("--remote-only", action="store_true")
    search_parser.add_argument("--limit", type=int, default=25)
    search_parser.set_defaults(func=cmd_search)

    applications_parser = subparsers.add_parser(
        "applications", help="List applications for an identity"
    )
    applications_parser.add_argument("identity_id")
    applications_parser.add_argument("--status", default=None)
    applications_parser.set_defaults(func=cmd_list)

    package_parser = subparsers.add_parser(
        "generate-package", help="Generate a resume/cover letter for a job URL"
    )
    package_parser.add_argument("identity_id")
    package_parser.add_argument("--job-url", required=True)
    package_parser.add_argument("--out-dir", default=None)
    package_parser.set_defaults(func=cmd_generate_package)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
