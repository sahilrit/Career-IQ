# LLM providers

CareerOS business logic never names a vendor. It asks the gateway
(`careeros_llm.LLMGateway`) for a **task**, and the gateway decides which
provider serves it.

## Why a gateway

The previous AI layer took one API key and called one HTTP endpoint. Without a
key, every AI feature resolved to `None` and quietly fell back to templates —
so someone running CareerOS locally with a paid Claude subscription got no AI
at all. That is the zero-paid-API goal failing in the exact case it exists for.

## Providers

| Kind | Ids | Needs |
|---|---|---|
| API key | `anthropic`, `openai`, `gemini`, `groq`, `openrouter`, `nvidia` | `CAREEROS_AI_API_KEY` (the vendor is inferred from the key's shape) |
| Agent CLI | `claude-cli`, `codex-cli`, `gemini-cli` | the binary on `PATH`, already logged in |

CLI ids carry a `-cli` suffix so they can never collide with the same vendor's
API-key provider in a priority list.

### The exit-0 trap

These CLIs can print `Not logged in · Please run /login` **and still exit 0**.
Returning that as the model's answer would be exactly the fabricated response
the architecture forbids, so banner-shaped output is turned into a real failure
carrying the fix.

### These CLIs are agents, not text completers

Left at their defaults, `claude -p` and `codex exec` can run shell commands and
edit files — that is what they are for. CareerOS uses them for one thing, and
the prompts it sends contain job descriptions fetched from the open internet,
which is precisely the input an attacker controls. So every CLI is invoked with
its tools switched off (`--disallowed-tools …` for Claude, `--sandbox read-only`
for Codex) rather than trusted not to use them.

## Provider states

A single generic "failed" was what made *"installed but never logged in"* and
*"never installed"* indistinguishable, leaving the user nothing to act on.
Health reports three facts separately — installed, authenticated, usable — plus
a reason and a remedy:

| Status | Meaning | Typical remedy |
|---|---|---|
| `available` | present, authenticated, answered a probe | — |
| `not_installed` | the executable is not on `PATH` | `npm install -g …` |
| `not_configured` | nothing configured at all (no API key) | set `CAREEROS_AI_API_KEY` |
| `not_authenticated` | present, but login/key rejected | `claude` → `/login` |
| `rate_limited` | authenticated, out of quota right now | wait, or use the fallback |
| `unavailable` | present and, as far as we can tell, fine — but no answer | retry later |
| `error` | the health check itself broke — a CareerOS bug, not a user problem | — |

`installed` and `authenticated` are booleans on `ProviderHealth`, not statuses:
a provider can be installed and still unusable, and `None` means "we could not
get far enough to tell", which is different from a definite `False`.

`gateway.provider_report()` covers every provider CareerOS knows about,
**including the ones absent from this machine** — a provider that is silently
missing from a list is one the user cannot act on:

```
codex-cli
  installed: no
  usable: no
  reason: `codex` is not on PATH
  fix: npm install -g @openai/codex
```

## Retryable vs non-retryable failures

`FailureKind` classifies every provider failure, and `is_retryable` governs
whether the SAME provider is worth re-asking. Moving to a *different* provider
is always allowed — it does not share the failure.

| Retryable | Not retryable |
|---|---|
| `timeout`, `network`, `malformed`, `unavailable` | `not_authenticated`, `not_installed`, `invalid_config`, `needs_human`, `rate_limited`, `unknown` |

`rate_limited` is deliberately in the right-hand column: an immediate retry hits
the same wall, so the fallback chain is the correct response rather than a
tighter loop. `unknown` is too, because an unrecognised failure repeated three
times is three times the damage if it is not actually transient.

## Structured output

Anywhere CareerOS needs a machine-readable answer — job analysis, question
classification, reviewer findings, scoring — free text is the wrong contract. A
model that answers *"roughly 7 out of 10"* where a float was expected does not
fail at the call site; it fails three functions later in code that has no idea
an LLM was involved.

```python
class JobAnalysis(BaseModel):
    qualified: bool
    score: int = Field(ge=0, le=100)

result = gateway.complete_structured(
    task=LLMTask.ANALYZE, system=..., prompt=..., schema=JobAnalysis
)
result.value.score  # an int, validated, or the call raised
```

The pipeline is **parse → validate → repair → fall back**. Output that fails
validation is never handed to a caller; the provider is re-asked once with the
validation error quoted back (the one retry that reliably helps), then abandoned
for the next provider in the chain. `try_complete_structured()` returns `None`
rather than a half-filled object.

## Tasks and routing

`LLMTask` values: `classify`, `extract`, `analyze`, `write`, `answer`,
`review`. Callers pick a task; config maps tasks to providers.

`review` deliberately prefers a **different** provider than `write`, so an
independent reviewer does not inherit the drafter's blind spots. With only one
provider configured the review still runs — a same-model review catches dates,
fabricated employers and missing fields, and is strictly better than none.

## Fallback

`complete()` walks the chain and records every rejection. If every provider
fails it raises `NoProviderAvailableError` carrying all the reasons. It never
returns an empty string or a placeholder that a caller could mistake for a real
answer.

Callers with a genuine deterministic fallback of their own use `try_complete()`,
which returns `None` rather than text — so a failure cannot be presented as a
generated answer.

## Configuration

```
CAREEROS_AI_API_KEY        one key; vendor inferred from its shape
CAREEROS_AI_MODEL          model override
CAREEROS_LLM_PRIORITY      comma-separated provider ids, best first
CAREEROS_LLM_CLI_ENABLED   0 to ignore locally installed CLIs
CAREEROS_LLM_TASK_REVIEW   pin one task to one provider (any LLMTask name)
```

A pinned provider is tried first for that task and the rest of the chain still
applies behind it, so pinning never turns a transient outage into a hard
failure.

## Health

```python
from careeros_llm import LLMGateway

gateway = LLMGateway.from_env()
for health in gateway.provider_report():   # every provider, present or not
    print(health.describe())
```

Details are written to be actionable — the command to run, not "error".

## Observability

Every call returns an `LLMRun`: task, provider, model, duration, fallbacks
tried, same-provider repair count, response length. It deliberately stores
**no prompt text**, because prompts contain the candidate's profile — and
there is no field on the model where that text could live, which is asserted
by a test rather than left as a convention.
