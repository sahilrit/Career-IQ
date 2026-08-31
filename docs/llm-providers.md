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
carrying the fix. This is why `health()` reports
`claude-cli  unavailable  Not logged in — run `claude` and use /login` rather
than a generic error.

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
for h in LLMGateway.from_env().health():
    print(h.provider_id, h.status.value, h.detail)
```

Details are written to be actionable — the command to run, not "error".

## Observability

Every call returns an `LLMRun`: task, provider, model, duration, fallbacks
tried, response length. It deliberately stores **no prompt text**, because
prompts contain the candidate's profile.
