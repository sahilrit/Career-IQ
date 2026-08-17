# Real AI generation — Slice 1 (AI foundation + AI cover letters)

**Date:** 2026-08-17
**Status:** approved design, pre-implementation
**Track:** Product Track 2 ("Real AI + money-maker"), slice 1 of 4.

## Goal

Replace template-only **cover-letter** generation with **real AI
(Anthropic Claude)** when the workspace has supplied its own API key,
while keeping the existing free template as the automatic fallback when
no key is present. Add the encrypted **key management** and a **Settings**
page that this (and every future AI feature) builds on.

**Scope note (tightened during spec review):** the earlier plan said
"cover letters + proposals". The cover-letter path has a real end-to-end
UI (Opportunities → Generate), so it proves real-AI end to end with the
least risk. The freelance *proposal* path has **no** generation endpoint
or screen yet, and the existing `ProposalGenerator` consumes a freelance
*gig* posting type that has no UI — building that flow belongs with the
Audit & Proposal money-maker slice (slice 4), where the matching inputs
and screen live. `careeros-ai` is built generically so the AI proposal
generator drops in there with almost no new plumbing.

**Cost model (decided):** bring-your-own-key. Each workspace stores its
own Anthropic API key; CareerOS never pays for AI. This matches the
repo's founding principle ("no mandatory paid API keys") and reuses the
existing `CredentialVault`.

## Non-goals (later slices)

- AI résumé parsing (slice 2), AI interview answers (slice 3), Audit &
  Proposal engine screen (slice 4).
- A shared/platform key or paid AI tiers. The design leaves room for it
  (the key-resolution seam) but builds none of it now.
- Streaming responses; official `anthropic` SDK (raw httpx is enough for
  one non-streaming completion and keeps the API image slim).

## Architecture

New thin package **`careeros-ai`** owns all LLM I/O — strings in, strings
out — and knows nothing about résumés or postings:

```
AIClient (Protocol):        complete(system: str, prompt: str) -> str
AnthropicClient(api_key, model):  calls Anthropic Messages API via httpx
AIError / AIAuthError / AIUnavailableError
```

Prompt-building and output stay in the domain package that already owns
the generator, so `careeros-ai` gains no domain dependencies:

- `careeros-application-engine` gains `AICoverLetterGenerator(client)`
  implementing the existing `CoverLetterGenerator` protocol. It adds a
  dependency on `careeros-ai` only.

It builds a **grounded** prompt from the `CareerBrain` + posting and a
**guardrail system prompt**: *use only the facts provided; never invent
employers, titles, metrics, or skills.*

(The parallel `AIProposalGenerator` for `careeros-opportunity-intelligence`
is built in slice 4 against the same `AIClient`; not in this slice.)

### Key storage

A small first-party wrapper around `CredentialVault` (in the API layer):

- service name: `"anthropic_api_key"`
- identity id: the workspace id (per-workspace, shared by members)
- requester id: `"careeros-app"` with a permission lookup that grants the
  first-party app the one credential permission it needs (the vault's
  `check_access` is designed for plugin manifests; the first-party app is
  authorized explicitly, not bypassed).
- cipher: `SecretCipher(os.environ["CAREEROS_SECRET_KEY"])` — a Fernet key.

### Selection ("picker")

The API `generate` path resolves the workspace key from the vault:

- key present → build `AnthropicClient` → `AICoverLetterGenerator`
- no key → `None` (defaults to `TemplateCoverLetterGenerator`)

`generate_application_for_job(store, identity_id, job_url)` gains an
optional `cover_letter_generator: CoverLetterGenerator | None = None`
threaded into the `build_application_package(..., cover_letter_generator=…)`
call it already supports. No behavior change when the arg is omitted.

If the AI call raises at generation time (timeout, quota, bad key), the
endpoint **falls back to the template** and reports `ai_used: false` so a
transient AI failure never blocks generation.

## API surface (careeros-api)

Settings (new `settings` router):

- `GET /settings/ai` → `{ "has_key": bool, "model": str }` — never returns
  the key itself.
- `PUT /settings/ai` `{ "api_key": str }` → validates prefix `sk-ant-`,
  stores encrypted, returns `{ "has_key": true }`. 422 on malformed input.
- `DELETE /settings/ai` → removes the key, returns `{ "has_key": false }`.
- Permission: `CAREER_BRAIN_WRITE` (owners/members yes, viewers no).

Generation (existing endpoint, augmented):

- `POST /opportunities/generate` → response gains `ai_used: bool`. The
  handler resolves the workspace key, injects `AICoverLetterGenerator`
  when present, else leaves the template default.

## Web (Next.js)

- New **`/settings`** page (also fills the missing Account/Settings gap):
  shows "AI: on/off" from `GET /settings/ai`, a password-type field to
  paste the key (save → `PUT`), and a Remove button (`DELETE`). Server
  route handlers under `web/app/api/settings/ai/` forward to the API with
  the httpOnly-cookie bearer token (same pattern as the résumé upload).
- Add **Settings** to the nav in `Shell.tsx`.
- Opportunities Generate: show a small "✨ AI-written" vs "Template" badge
  from `ai_used`. No other UI change.

## Config / deployment

- New env **`CAREEROS_SECRET_KEY`** (Fernet key) for the cipher. Add to
  `render.yaml` for `careeros-api` with `generateValue: true` so it is
  created once and stays stable. **Losing/rotating it makes stored keys
  undecryptable** — documented in the runbook. Local dev: if unset, fall
  back to a dev key derived deterministically so tests/local run without
  setup (never used in prod, which sets the env).
- Optional **`CAREEROS_AI_MODEL`** (default `claude-haiku-4-5-20251001` —
  cheap and fast, right for a user paying per call).
- `careeros-ai` depends on `httpx` (already in the lock). Add
  `careeros-ai` to `careeros-api` deps so the client ships in the image.

## Error handling

- Bad key on `PUT`: format-checked synchronously; a live validation call
  is optional and, if added, maps a 401 from Anthropic to a clear 422.
- Generation-time AI failure: caught, fall back to template, `ai_used:
  false`. Never 500 because of AI.
- Missing `CAREEROS_SECRET_KEY` in prod: the settings write fails loudly
  (misconfiguration), not silently.

## Testing (no real API calls in CI)

- `careeros-ai`: `AnthropicClient` against a mocked httpx transport —
  success parse, 401 → `AIAuthError`, 5xx/timeout → `AIUnavailableError`.
- `careeros-application-engine`: `AICoverLetterGenerator` with a fake
  `AIClient` returning canned prose — assert the grounded prompt carries
  the brain's facts and the output is returned; assert protocol
  conformance.
- `careeros-api`: `/settings/ai` store→has→delete round trip and auth
  gating; `generate` returns `ai_used: true` with a fake client injected
  and `ai_used: false` (template) when no key; AI exception → template
  fallback.

## Rollout

Ships behind the presence of a key: with no key set anywhere, behavior is
byte-for-byte today's templates. Sahil creates an Anthropic key, pastes it
in Settings, and generation becomes AI — reversible by removing the key.
