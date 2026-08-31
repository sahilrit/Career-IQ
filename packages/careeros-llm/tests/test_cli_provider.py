"""CliProvider: the contract that keeps a CLI banner from becoming an 'answer'."""

from __future__ import annotations

import subprocess

import pytest

from careeros_llm import (
    CliProvider,
    CliSpec,
    ProviderCallError,
    ProviderStatus,
    looks_like_cli_error,
)

SPEC = CliSpec(
    "fakecli",
    "fakecli",
    prompt_flag="-p",
    model_flag="--model",
    default_model="fake-model",
    login_hint="run `fakecli login`",
)


def runner_returning(code: int, out: str, err: str = "", *, record: list | None = None):
    def run(argv, input_text, timeout):
        if record is not None:
            record.append((argv, input_text, timeout))
        return code, out, err

    return run


def provider(runner, **kwargs) -> CliProvider:
    p = CliProvider(SPEC, runner=runner, **kwargs)
    # The binary does not exist on the test machine; the point of these tests is
    # the response contract, so resolution is stubbed to a fixed path.
    p._resolve_executable = lambda: "/usr/bin/fakecli"
    return p


class TestLooksLikeCliError:
    @pytest.mark.parametrize(
        "text",
        [
            "Not logged in · Please run /login",
            "Please set an Auth method in your settings.json",
            "Error: invalid API key",
            "usage limit reached, try again later",
        ],
    )
    def test_recognizes_banners(self, text):
        assert looks_like_cli_error(text) is not None

    def test_empty_output_is_an_error(self):
        assert looks_like_cli_error("   ") == "the CLI produced no output"

    def test_a_real_answer_is_not_an_error(self):
        assert looks_like_cli_error("Yes, I am authorized to work in the US.") is None

    def test_long_text_mentioning_a_marker_is_not_an_error(self):
        # A cover letter may legitimately discuss rate limits; only short
        # banner-shaped output is treated as a failure.
        essay = "I built a rate limit service. " * 40
        assert len(essay) > 400
        assert looks_like_cli_error(essay) is None


class TestComplete:
    def test_returns_stdout(self):
        assert (
            provider(runner_returning(0, "  the answer  ")).complete(system="s", prompt="p")
            == "the answer"
        )

    def test_exit_zero_login_banner_raises_with_the_login_hint(self):
        # The real trap: `claude -p` exits 0 while printing this.
        with pytest.raises(ProviderCallError) as exc:
            provider(runner_returning(0, "Not logged in · Please run /login")).complete(
                system="s", prompt="p"
            )
        assert "Not logged in" in str(exc.value)
        assert "fakecli login" in str(exc.value)

    def test_nonzero_exit_raises(self):
        with pytest.raises(ProviderCallError, match="exited 1"):
            provider(runner_returning(1, "", "boom")).complete(system="s", prompt="p")

    def test_timeout_raises(self):
        def timing_out(argv, input_text, timeout):
            raise subprocess.TimeoutExpired(argv, timeout)

        with pytest.raises(ProviderCallError, match="timed out"):
            provider(timing_out).complete(system="s", prompt="p")

    def test_missing_binary_raises_rather_than_returning_empty(self):
        p = CliProvider(SPEC, runner=runner_returning(0, "x"))
        p._resolve_executable = lambda: None
        with pytest.raises(ProviderCallError, match="not installed"):
            p.complete(system="s", prompt="p")

    def test_system_prompt_is_passed_through_not_dropped(self):
        calls: list = []
        provider(runner_returning(0, "ok", record=calls)).complete(
            system="BE TRUTHFUL", prompt="the question"
        )
        argv = calls[0][0]
        assert "BE TRUTHFUL" in argv[2]
        assert "the question" in argv[2]

    def test_model_flag_is_included(self):
        calls: list = []
        provider(runner_returning(0, "ok", record=calls)).complete(system="", prompt="p")
        assert calls[0][0][-2:] == ["--model", "fake-model"]


class TestHealthCheck:
    def test_absent_when_not_installed(self):
        p = CliProvider(SPEC, runner=runner_returning(0, "ok"))
        p._resolve_executable = lambda: None
        health = p.health_check()
        assert health.status is ProviderStatus.ABSENT
        assert "not installed" in health.detail

    def test_not_authenticated_when_not_logged_in(self):
        # Deliberately NOT the same status as "the CLI did not answer": an
        # unauthenticated CLI is one command away from working and the user
        # has to be told which command.
        health = provider(runner_returning(0, "Not logged in · Please run /login")).health_check()
        assert health.status is ProviderStatus.NOT_AUTHENTICATED
        assert "fakecli login" in health.detail

    def test_healthy_when_it_answers(self):
        assert provider(runner_returning(0, "OK")).health_check().status is ProviderStatus.HEALTHY
