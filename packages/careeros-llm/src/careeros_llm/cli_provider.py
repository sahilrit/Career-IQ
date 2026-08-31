"""CliProvider: use a locally authenticated agent CLI as an LLM provider.

This is the zero-paid-API path. A user who already pays for Claude or Gemini
has a working, authenticated model on their machine; making CareerOS able to
call it means the product never *requires* anyone to buy an API key.

Two things make this harder than "shell out and read stdout", and both are
handled here because both were observed on a real machine:

1. **These CLIs exit 0 when they are not logged in.** ``claude -p '…'`` prints
   ``Not logged in · Please run /login`` and returns status 0. A naive wrapper
   would hand that sentence back as the model's answer — which is exactly the
   "fake AI response" the architecture forbids. ``_looks_like_cli_error``
   catches those banners and turns them into a real failure.
2. **They are slow to start.** A cold agent CLI can take many seconds before
   the first token, so the timeout is generous and configurable rather than
   the few seconds an HTTP call would use.
"""

from __future__ import annotations

import shutil
import subprocess

from careeros_common import get_logger
from careeros_llm.exceptions import ProviderCallError
from careeros_llm.models import ProviderHealth, ProviderStatus

logger = get_logger(__name__)

#: Agent CLIs boot a whole runtime before answering; 180s is not generous, it
#: is realistic. Overridable per provider.
DEFAULT_CLI_TIMEOUT_SECONDS = 180.0

_PROBE_SYSTEM = "You are a health probe. Reply with exactly one word."
_PROBE_PROMPT = "Reply with exactly: OK"

#: Substrings that mean "the CLI ran but did not answer as a model". Matched
#: case-insensitively against a SHORT response — a long answer that happens to
#: discuss logging in is a real answer, not a banner (see _looks_like_cli_error).
_CLI_ERROR_MARKERS = (
    "not logged in",
    "please run /login",
    "please set an auth method",
    "no auth method",
    "authentication required",
    "invalid api key",
    "api key not found",
    "quota exceeded",
    "rate limit",
    "usage limit reached",
    "command not found",
)

#: A banner is short. Above this length we assume we are looking at a genuine
#: answer and do not pattern-match it, so a cover letter mentioning "rate
#: limit" is never mistaken for an error.
_BANNER_MAX_CHARS = 400


def looks_like_cli_error(text: str) -> str | None:
    """The error a CLI reported in place of an answer, or None.

    Returns the matched marker so the caller can put something actionable in
    front of the user instead of a generic failure.
    """
    stripped = (text or "").strip()
    if not stripped:
        return "the CLI produced no output"
    if len(stripped) > _BANNER_MAX_CHARS:
        return None
    lowered = stripped.lower()
    for marker in _CLI_ERROR_MARKERS:
        if marker in lowered:
            return stripped.splitlines()[0][:200]
    return None


class CliSpec:
    """How to drive one agent CLI in non-interactive mode."""

    def __init__(
        self,
        provider_id: str,
        executable: str,
        *,
        prompt_flag: str,
        model_flag: str | None = None,
        default_model: str = "",
        login_hint: str = "",
        extra_args: tuple[str, ...] = (),
    ) -> None:
        self.provider_id = provider_id
        self.executable = executable
        self.prompt_flag = prompt_flag
        self.model_flag = model_flag
        self.default_model = default_model
        self.login_hint = login_hint
        self.extra_args = extra_args


#: The CLIs CareerOS knows how to drive. Adding another is one entry here.
#: CLI provider ids are SUFFIXED with -cli so they can never collide with an
#: API-key provider of the same vendor ("gemini" the API key vs "gemini" the
#: locally installed CLI). Without the suffix a priority list could not express
#: "prefer the Gemini API over the Gemini CLI", and health output was ambiguous
#: about which of the two it was describing.
CLI_SPECS: dict[str, CliSpec] = {
    "claude-cli": CliSpec(
        "claude-cli",
        "claude",
        prompt_flag="-p",
        model_flag="--model",
        default_model="claude-haiku-4-5-20251001",
        login_hint="run `claude` and use /login to authenticate",
    ),
    "codex-cli": CliSpec(
        "codex-cli",
        "codex",
        prompt_flag="exec",
        model_flag="--model",
        default_model="",
        login_hint="run `codex login` to authenticate",
    ),
    "gemini-cli": CliSpec(
        "gemini-cli",
        "gemini",
        prompt_flag="-p",
        model_flag="--model",
        default_model="",
        login_hint=("set GEMINI_API_KEY, or configure an auth method in ~/.gemini/settings.json"),
    ),
}


class CliProvider:
    """An agent CLI (already authenticated on this machine) as an LLM provider."""

    def __init__(
        self,
        spec: CliSpec,
        *,
        model: str | None = None,
        timeout_seconds: float = DEFAULT_CLI_TIMEOUT_SECONDS,
        runner=None,
    ) -> None:
        self._spec = spec
        self._model = model or spec.default_model
        self._timeout = timeout_seconds
        #: Injected in tests so the CLI contract can be exercised without a
        #: real binary. Signature: (argv, input_text, timeout) -> (rc, out, err)
        self._runner = runner or self._run_subprocess

    @property
    def provider_id(self) -> str:
        return self._spec.provider_id

    @property
    def model(self) -> str:
        return self._model

    def _resolve_executable(self) -> str | None:
        return shutil.which(self._spec.executable)

    def _run_subprocess(
        self, argv: list[str], input_text: str, timeout: float
    ) -> tuple[int, str, str]:
        completed = subprocess.run(
            argv,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr

    def _build_argv(self, combined_prompt: str) -> list[str]:
        argv = [self._spec.executable, self._spec.prompt_flag, combined_prompt]
        if self._model and self._spec.model_flag:
            argv += [self._spec.model_flag, self._model]
        argv += list(self._spec.extra_args)
        return argv

    def complete(self, *, system: str, prompt: str) -> str:
        if self._resolve_executable() is None:
            raise ProviderCallError(
                self.provider_id, f"`{self._spec.executable}` is not installed on this machine"
            )
        # These CLIs take one prompt string, not a system/user pair. Prefixing
        # the system instruction is the honest equivalent: the model still sees
        # it first and as an instruction, and nothing is silently dropped.
        combined = f"{system}\n\n{prompt}" if system else prompt
        argv = self._build_argv(combined)
        try:
            code, out, err = self._runner(argv, "", self._timeout)
        except subprocess.TimeoutExpired as exc:
            raise ProviderCallError(
                self.provider_id, f"timed out after {self._timeout:g}s"
            ) from exc
        except OSError as exc:
            raise ProviderCallError(self.provider_id, f"could not run the CLI: {exc}") from exc

        text = (out or "").strip()
        if code != 0:
            detail = (err or text or "no output").strip().splitlines()
            raise ProviderCallError(
                self.provider_id, f"exited {code}: {detail[0][:200] if detail else 'no output'}"
            )
        # The exit-0-with-an-error-banner case. Without this the banner would
        # be returned as if it were the model's answer.
        banner = looks_like_cli_error(text)
        if banner is not None:
            hint = f" — {self._spec.login_hint}" if self._spec.login_hint else ""
            raise ProviderCallError(self.provider_id, f"{banner}{hint}")
        return text

    def health_check(self) -> ProviderHealth:
        if self._resolve_executable() is None:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.ABSENT,
                detail=f"`{self._spec.executable}` is not installed",
                model=self._model,
            )
        try:
            self.complete(system=_PROBE_SYSTEM, prompt=_PROBE_PROMPT)
        except ProviderCallError as exc:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderStatus.UNAVAILABLE,
                detail=str(exc),
                model=self._model,
            )
        return ProviderHealth(
            provider_id=self.provider_id, status=ProviderStatus.HEALTHY, model=self._model
        )


def available_cli_providers(**kwargs) -> list[CliProvider]:
    """One provider per known CLI that is actually installed here.

    Installed, not authenticated — the gateway's health check draws that line,
    because it is the one that can tell the user which command to run.
    """
    return [
        CliProvider(spec, **kwargs)
        for spec in CLI_SPECS.values()
        if shutil.which(spec.executable) is not None
    ]
