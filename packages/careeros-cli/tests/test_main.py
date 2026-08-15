"""Tests for the argparse wiring and end-to-end `main()` dispatch.

Only exercises commands that never touch the network through main()
(brain/applications) — search and generate-package are covered via their
pure logic functions against a fake provider in their own test modules,
since going through main() would construct the real RemoteOKProvider.
"""

from __future__ import annotations

from careeros_cli.main import build_parser, main


def test_parser_wires_every_subcommand():
    parser = build_parser()

    brain_args = parser.parse_args(
        ["brain", "create", "--full-name", "Ada", "--email", "ada@example.com"]
    )
    assert brain_args.command == "brain"
    assert brain_args.brain_command == "create"

    search_args = parser.parse_args(["search", "some-id"])
    assert search_args.command == "search"

    applications_args = parser.parse_args(["applications", "some-id"])
    assert applications_args.command == "applications"

    package_args = parser.parse_args(
        ["generate-package", "some-id", "--job-url", "https://example.com/1"]
    )
    assert package_args.command == "generate-package"


def test_brain_create_then_show_round_trip(tmp_path, capsys):
    exit_code = main(
        [
            "--data-dir",
            str(tmp_path),
            "brain",
            "create",
            "--full-name",
            "Ada Lovelace",
            "--email",
            "ada@example.com",
            "--headline",
            "Engineer",
        ]
    )
    assert exit_code == 0
    identity_id = capsys.readouterr().out.strip()

    exit_code = main(["--data-dir", str(tmp_path), "brain", "show", identity_id])
    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Ada Lovelace <ada@example.com>" in output


def test_brain_show_missing_identity_returns_error_exit_code(tmp_path, capsys):
    exit_code = main(["--data-dir", str(tmp_path), "brain", "show", "does-not-exist"])
    assert exit_code == 1
    assert "No Career Brain found" in capsys.readouterr().err


def test_applications_on_a_brain_with_none_prints_nothing(tmp_path, capsys):
    main(
        [
            "--data-dir",
            str(tmp_path),
            "brain",
            "create",
            "--full-name",
            "Ada Lovelace",
            "--email",
            "ada@example.com",
        ]
    )
    identity_id = capsys.readouterr().out.strip()

    exit_code = main(["--data-dir", str(tmp_path), "applications", identity_id])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == ""
