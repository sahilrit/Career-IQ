"""Provider states must stay distinguishable.

The bug this file exists to prevent: every unusable provider reporting the
same generic failure, so "claude is installed but you never logged in" and
"claude was never installed" were indistinguishable and neither told the user
what to do.
"""

from __future__ import annotations

import pytest

from careeros_llm import (
    ApiKeyProvider,
    CliProvider,
    CliSpec,
    FailureKind,
    LLMGateway,
    ProviderCallError,
    ProviderStatus,
    classify_failure,
)
from careeros_llm.config import LLMConfig


def spec(**kwargs) -> CliSpec:
    defaults = {
        "prompt_flag": "-p",
        "login_hint": "run `fake login`",
        "install_hint": "npm i -g fake",
    }
    return CliSpec("fake-cli", "fake", **{**defaults, **kwargs})


def provider(runner, *, executable_found: bool = True) -> CliProvider:
    made = CliProvider(spec(), runner=runner, timeout_seconds=1)
    if not executable_found:
        made._resolve_executable = lambda: None
    else:
        made._resolve_executable = lambda: "/usr/bin/fake"
    return made


def returning(code: int, out: str, err: str = ""):
    return lambda argv, text, timeout: (code, out, err)


class TestFailureClassification:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("Not logged in · Please run /login", FailureKind.NOT_AUTHENTICATED),
            ("invalid api key provided", FailureKind.NOT_AUTHENTICATED),
            ("You have exceeded your quota exceeded limit", FailureKind.RATE_LIMITED),
            ("429 too many requests", FailureKind.RATE_LIMITED),
            ("`codex` is not installed on this machine", FailureKind.NOT_INSTALLED),
            ("timed out after 180s", FailureKind.TIMEOUT),
            ("connection reset by peer", FailureKind.NETWORK),
            ("unknown model banana-2", FailureKind.INVALID_CONFIG),
            ("something nobody has ever seen", FailureKind.UNKNOWN),
        ],
    )
    def test_messages_are_classified(self, message, expected):
        assert classify_failure(message) is expected

    def test_only_transient_kinds_are_retryable(self):
        assert FailureKind.TIMEOUT.is_retryable
        assert FailureKind.NETWORK.is_retryable
        assert FailureKind.MALFORMED.is_retryable
        # Retrying these against the same provider can never succeed.
        assert not FailureKind.NOT_AUTHENTICATED.is_retryable
        assert not FailureKind.NOT_INSTALLED.is_retryable
        assert not FailureKind.INVALID_CONFIG.is_retryable
        assert not FailureKind.NEEDS_HUMAN.is_retryable

    def test_rate_limit_is_not_retried_against_the_same_provider(self):
        # An immediate retry hits the same wall; the fallback chain is the
        # correct response, not a tighter loop.
        assert not FailureKind.RATE_LIMITED.is_retryable

    def test_unknown_is_not_retryable_by_default(self):
        assert not FailureKind.UNKNOWN.is_retryable

    def test_error_infers_its_kind_from_the_message(self):
        error = ProviderCallError("claude-cli", "Not logged in · Please run /login")
        assert error.kind is FailureKind.NOT_AUTHENTICATED
        assert not error.is_retryable


class TestCliProviderStates:
    def test_not_installed_is_distinct_and_says_how_to_install(self):
        health = provider(returning(0, "OK"), executable_found=False).health_check()
        assert health.status is ProviderStatus.NOT_INSTALLED
        assert health.installed is False
        # Never claimed to be unauthenticated — we could not get far enough
        # to know, and pretending otherwise sends the user to the wrong fix.
        assert health.authenticated is None
        assert not health.usable
        assert "npm i -g fake" in health.remedy

    def test_installed_but_not_logged_in_is_its_own_state(self):
        health = provider(returning(0, "Not logged in · Please run /login")).health_check()
        assert health.status is ProviderStatus.NOT_AUTHENTICATED
        assert health.installed is True
        assert health.authenticated is False
        assert not health.usable
        assert "fake login" in health.remedy

    def test_rate_limited_is_not_reported_as_a_login_problem(self):
        health = provider(returning(0, "usage limit reached")).health_check()
        assert health.status is ProviderStatus.RATE_LIMITED
        assert health.installed is True
        # A rate limit proves the credentials WORK.
        assert health.authenticated is None
        assert not health.usable

    def test_timeout_is_transient_not_a_user_problem(self):
        import subprocess

        def timing_out(argv, text, timeout):
            raise subprocess.TimeoutExpired(argv, timeout)

        health = provider(timing_out).health_check()
        assert health.status is ProviderStatus.UNAVAILABLE
        assert health.installed is True
        assert health.authenticated is None

    def test_working_cli_is_available_and_authenticated(self):
        health = provider(returning(0, "OK")).health_check()
        assert health.status is ProviderStatus.AVAILABLE
        assert health.usable
        assert health.installed is True
        assert health.authenticated is True

    def test_describe_reports_the_three_facts_separately(self):
        text = provider(returning(0, "Not logged in")).health_check().describe()
        assert "installed: yes" in text
        assert "authenticated: no" in text
        assert "usable: no" in text
        assert "reason:" in text


class TestApiKeyProviderStates:
    def test_no_key_is_not_configured_rather_than_absent_hardware(self):
        health = ApiKeyProvider("").health_check()
        assert health.status is ProviderStatus.NOT_CONFIGURED
        # A hosted API is never "installed" — claiming False would read as a
        # missing package the user could go and install.
        assert health.installed is None
        assert not health.usable
        assert "CAREEROS_AI_API_KEY" in health.remedy


class TestGatewayProviderReport:
    def test_report_covers_providers_that_are_absent_entirely(self):
        # No API key, no CLIs on this machine: the report must still name every
        # provider CareerOS knows about, with a reason and a remedy.
        gateway = LLMGateway(providers=[], config=LLMConfig(api_key="", cli_enabled=False))
        report = {health.provider_id: health for health in gateway.provider_report()}

        assert {"claude-cli", "codex-cli", "gemini-cli", "api-key"} <= set(report)
        for health in report.values():
            assert not health.usable
            assert health.detail, f"{health.provider_id} gave no reason"

    def test_absent_cli_reports_not_installed_with_an_install_command(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda name: None)
        gateway = LLMGateway(providers=[], config=LLMConfig(api_key=""))
        report = {health.provider_id: health for health in gateway.provider_report()}
        codex = report["codex-cli"]
        assert codex.status is ProviderStatus.NOT_INSTALLED
        assert codex.installed is False
        assert codex.remedy

    def test_health_check_that_raises_is_an_error_not_a_login_problem(self):
        class Exploding:
            provider_id = "boom"
            model = "m"

            def complete(self, *, system, prompt):
                return ""

            def health_check(self):
                raise RuntimeError("kaboom")

        health = LLMGateway(providers=[Exploding()]).health()[0]
        assert health.status is ProviderStatus.ERROR
        assert "kaboom" in health.detail


class TestCliProvidersCannotActOnTheMachine:
    """These CLIs are AGENTS, not text completers.

    Left at their defaults, a "text completion" can run shell commands and edit
    files. The prompts CareerOS sends contain job descriptions fetched from the
    open internet — exactly the input an attacker controls — so the tools are
    switched off at the command line rather than trusted not to fire.
    """

    def test_claude_is_invoked_with_its_tools_disabled(self):
        from careeros_llm import CLI_SPECS

        args = CLI_SPECS["claude-cli"].extra_args
        assert "--disallowed-tools" in args
        blocked = args[args.index("--disallowed-tools") + 1]
        for tool in ("Bash", "Edit", "Write", "WebFetch"):
            assert tool in blocked, tool

    def test_codex_is_invoked_in_a_read_only_sandbox(self):
        from careeros_llm import CLI_SPECS

        args = CLI_SPECS["codex-cli"].extra_args
        assert "--sandbox" in args
        assert args[args.index("--sandbox") + 1] == "read-only"

    def test_the_restriction_actually_reaches_the_command_line(self):
        from careeros_llm import CLI_SPECS, CliProvider

        calls: list = []
        made = CliProvider(
            CLI_SPECS["claude-cli"],
            runner=lambda argv, text, timeout: (calls.append(argv), (0, "ok", ""))[1],
        )
        made._resolve_executable = lambda: "/usr/bin/claude"
        made.complete(system="s", prompt="p")
        assert "--disallowed-tools" in calls[0]
