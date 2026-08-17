# Real AI Generation — Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate cover letters with real AI (Anthropic Claude) when a workspace supplies its own API key, falling back to the existing free template otherwise, with encrypted key storage and a Settings page.

**Architecture:** A thin `careeros-ai` package owns all LLM I/O (strings in, strings out). `AICoverLetterGenerator` implements the existing `CoverLetterGenerator` protocol using it. The API resolves the workspace's encrypted key from `CredentialVault` and injects the AI generator into the existing generate path, else leaves the template default. A new Settings page manages the key.

**Tech Stack:** Python 3.12, FastAPI, httpx, pydantic, `cryptography` (Fernet via existing `SecretCipher`), Next.js 14 App Router, uv workspace.

**Spec:** `docs/superpowers/specs/2026-08-17-real-ai-generation-design.md`

## Global Constraints

- Bring-your-own-key: CareerOS never pays for AI. No behavior change when no key is set (byte-for-byte today's template).
- No real network calls to Anthropic in any test — inject fakes / mock httpx transport.
- Encryption key from env `CAREEROS_SECRET_KEY` (Fernet); deterministic dev fallback when unset (never in prod).
- Default model `claude-haiku-4-5-20251001`, overridable via env `CAREEROS_AI_MODEL`.
- Vault service name: `"anthropic_api_key"`; requester id: `"careeros-app"`; identity id: the workspace id.
- Guardrail system prompt: use only provided facts; never invent employers, titles, metrics, or skills.
- Follow existing patterns: `Annotated[...]` FastAPI deps (no `File(...)`/`Depends()` in defaults → B008); ruff clean; `uv run pytest` green.

---

### Task 1: `careeros-ai` package (AIClient + AnthropicClient)

**Files:**
- Create: `packages/careeros-ai/pyproject.toml`
- Create: `packages/careeros-ai/src/careeros_ai/__init__.py`
- Create: `packages/careeros-ai/src/careeros_ai/client.py`
- Create: `packages/careeros-ai/src/careeros_ai/anthropic_client.py`
- Test: `packages/careeros-ai/tests/test_anthropic_client.py`
- Modify: root `pyproject.toml` workspace members already glob `packages/*`; run `uv lock`.

**Interfaces:**
- Produces: `AIClient` protocol `complete(self, *, system: str, prompt: str) -> str`; `AnthropicClient(api_key: str, model: str = "claude-haiku-4-5-20251001", *, http_client: httpx.Client | None = None)`; errors `AIError`, `AIAuthError(AIError)`, `AIUnavailableError(AIError)`. `DEFAULT_MODEL: str`.

- [ ] **Step 1: Write `client.py`** (protocol + errors)

```python
"""AIClient: the one seam every AI feature calls. Strings in, strings out —
it knows nothing about résumés, postings, or the domain."""

from __future__ import annotations
from typing import Protocol

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AIError(Exception):
    """Base for all AI client failures."""


class AIAuthError(AIError):
    """The API key was rejected (401/403)."""


class AIUnavailableError(AIError):
    """Timeout, rate limit, or 5xx — transient; callers fall back."""


class AIClient(Protocol):
    def complete(self, *, system: str, prompt: str) -> str: ...
```

- [ ] **Step 2: Write the failing test** `test_anthropic_client.py`

```python
import httpx
import pytest
from careeros_ai import AnthropicClient, AIAuthError, AIUnavailableError


def _transport(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_complete_returns_text():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "sk-ant-test"
        assert request.headers["anthropic-version"]
        return httpx.Response(200, json={"content": [{"type": "text", "text": "Dear Team,"}]})

    client = AnthropicClient("sk-ant-test", http_client=_transport(handler))
    assert client.complete(system="s", prompt="p") == "Dear Team,"


def test_401_raises_auth_error():
    client = AnthropicClient(
        "bad", http_client=_transport(lambda r: httpx.Response(401, json={"error": {}}))
    )
    with pytest.raises(AIAuthError):
        client.complete(system="s", prompt="p")


def test_500_raises_unavailable():
    client = AnthropicClient(
        "sk-ant-x", http_client=_transport(lambda r: httpx.Response(529, json={}))
    )
    with pytest.raises(AIUnavailableError):
        client.complete(system="s", prompt="p")
```

- [ ] **Step 3: Run test to verify it fails** — `uv run pytest packages/careeros-ai -q` → FAIL (import error).

- [ ] **Step 4: Write `anthropic_client.py`**

```python
"""AnthropicClient: a minimal Messages API caller over httpx (no SDK, to
keep the API image slim). One non-streaming completion per call."""

from __future__ import annotations
import httpx
from careeros_ai.client import AIAuthError, AIUnavailableError, DEFAULT_MODEL

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"


class AnthropicClient:
    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, *, http_client: httpx.Client | None = None
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._http = http_client or httpx.Client(timeout=60.0)

    def complete(self, *, system: str, prompt: str) -> str:
        try:
            response = self._http.post(
                _URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        except httpx.HTTPError as error:
            raise AIUnavailableError(str(error)) from error
        if response.status_code in (401, 403):
            raise AIAuthError("Anthropic rejected the API key")
        if response.status_code >= 500 or response.status_code == 429:
            raise AIUnavailableError(f"Anthropic returned {response.status_code}")
        if response.status_code >= 400:
            raise AIUnavailableError(
                f"Anthropic returned {response.status_code}: {response.text[:200]}"
            )
        blocks = response.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
```

- [ ] **Step 5: Write `__init__.py`**

```python
from careeros_ai.anthropic_client import AnthropicClient
from careeros_ai.client import (
    DEFAULT_MODEL,
    AIAuthError,
    AIClient,
    AIError,
    AIUnavailableError,
)

__all__ = [
    "DEFAULT_MODEL",
    "AIAuthError",
    "AIClient",
    "AIError",
    "AIUnavailableError",
    "AnthropicClient",
]
```

- [ ] **Step 6: Write `pyproject.toml`** (mirror an existing leaf package)

```toml
[project]
name = "careeros-ai"
version = "0.1.0"
description = "AIClient seam: the single place CareerOS talks to an LLM (Anthropic Claude by default)."
requires-python = ">=3.12"
dependencies = ["httpx>=0.27"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/careeros_ai"]
```

- [ ] **Step 7: Lock, sync, test** — `uv lock && uv sync --all-packages && uv run pytest packages/careeros-ai -q` → PASS. `uv run ruff check packages/careeros-ai && uv run ruff format packages/careeros-ai`.

- [ ] **Step 8: Commit** — `git add -A && git commit -m "feat(ai): careeros-ai package with Anthropic client seam"`

---

### Task 2: `AICoverLetterGenerator`

**Files:**
- Create: `packages/careeros-application-engine/src/careeros_application_engine/ai_cover_letter.py`
- Modify: `packages/careeros-application-engine/src/careeros_application_engine/__init__.py` (export it)
- Modify: `packages/careeros-application-engine/pyproject.toml` (add `careeros-ai` dep + workspace source)
- Test: `packages/careeros-application-engine/tests/test_ai_cover_letter.py`

**Interfaces:**
- Consumes: `AIClient` from Task 1; existing `CoverLetterGenerator` protocol, `CareerBrain`, `JobPosting`.
- Produces: `AICoverLetterGenerator(client: AIClient)` with `.generate(brain: CareerBrain, posting: JobPosting) -> str`.

- [ ] **Step 1: Write the failing test**

```python
from careeros_application_engine import AICoverLetterGenerator
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_job_providers import JobPosting


class FakeClient:
    def __init__(self):
        self.calls = []

    def complete(self, *, system, prompt):
        self.calls.append((system, prompt))
        return "AI cover letter."


def _brain():
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="a@x.com", summary="Growth marketer."),
        skills=[Skill(name="Meta Ads")],
    )


def _posting():
    return JobPosting(
        title="PPC Manager",
        company_name="Acme",
        url="https://acme.com/j/1",
        description="Run paid campaigns.",
        source="test",
    )


def test_uses_ai_and_grounds_prompt_in_brain():
    fake = FakeClient()
    out = AICoverLetterGenerator(fake).generate(_brain(), _posting())
    assert out == "AI cover letter."
    system, prompt = fake.calls[0]
    assert "never invent" in system.lower()
    assert "Ada Lovelace" in prompt and "Meta Ads" in prompt and "Acme" in prompt
```

- [ ] **Step 2: Run test → FAIL.** `uv run pytest packages/careeros-application-engine/tests/test_ai_cover_letter.py -q`

- [ ] **Step 3: Write `ai_cover_letter.py`** — verify exact `JobPosting` field names first with `grep -n "class JobPosting" -A15 packages/careeros-job-providers/src/careeros_job_providers/*.py` and adjust the prompt accordingly.

```python
"""AICoverLetterGenerator: same CoverLetterGenerator seam as the template
one, but the prose comes from an AIClient, grounded strictly in Career Brain."""

from __future__ import annotations
from careeros_ai import AIClient
from careeros_career_brain import CareerBrain
from careeros_job_providers import JobPosting

_SYSTEM = (
    "You write concise, specific cover letters. Use ONLY the facts provided "
    "about the candidate and role. Never invent employers, job titles, metrics, "
    "skills, or achievements. 180-260 words, professional, no placeholders."
)


class AICoverLetterGenerator:
    def __init__(self, client: AIClient) -> None:
        self._client = client

    def generate(self, brain: CareerBrain, posting: JobPosting) -> str:
        prompt = self._prompt(brain, posting)
        return self._client.complete(system=_SYSTEM, prompt=prompt).strip() + "\n"

    def _prompt(self, brain: CareerBrain, posting: JobPosting) -> str:
        i = brain.identity
        skills = ", ".join(s.name for s in brain.skills) or "(none listed)"
        experiences = (
            "\n".join(f"- {e.title} at {e.company_name}" for e in brain.experiences)
            or "(none listed)"
        )
        return (
            f"Candidate: {i.full_name}\n"
            f"Headline: {i.headline}\n"
            f"Summary: {i.summary}\n"
            f"Skills: {skills}\n"
            f"Experience:\n{experiences}\n\n"
            f"Role: {posting.title} at {posting.company_name}\n"
            f"Job description:\n{posting.description}\n\n"
            f"Write the cover letter, signed '{i.full_name}'."
        )
```

- [ ] **Step 4: Export from `__init__.py`** — add `from careeros_application_engine.ai_cover_letter import AICoverLetterGenerator` and to `__all__`.

- [ ] **Step 5: Add dep** in `pyproject.toml`: add `"careeros-ai"` to `dependencies` and `careeros-ai = { workspace = true }` to `[tool.uv.sources]`. Then `uv lock && uv sync --all-packages`.

- [ ] **Step 6: Run test → PASS.** ruff check + format the package.

- [ ] **Step 7: Commit** — `git commit -am "feat(ai): AICoverLetterGenerator grounded in Career Brain"`

---

### Task 3: Thread an injectable generator through `generate_application_for_job`

**Files:**
- Modify: `packages/careeros-job-search/src/careeros_job_search/__init__.py` (the `generate_application_for_job` function)
- Test: `packages/careeros-job-search/tests/test_generate_injection.py` (create)

**Interfaces:**
- Consumes: existing `build_application_package(brain, posting, *, cover_letter_generator=None)`.
- Produces: `generate_application_for_job(store, identity_id, job_url, *, provider_registry=None, cover_letter_generator: CoverLetterGenerator | None = None)`.

- [ ] **Step 1: Write failing test** — seed a brain + cached posting in a store, pass a fake generator, assert the returned package's `cover_letter == "INJECTED"`.

```python
from careeros_job_search import generate_application_for_job
# (build a store via careeros_common.open_store with a tmp CAREEROS_DATA_DIR;
#  seed CareerBrain via CareerBrainRepository and a JobPosting via JobPostingRepository,
#  mirroring packages/careeros-job-search/tests existing fixtures)


class FakeGen:
    def generate(self, brain, posting):
        return "INJECTED"


def test_generate_uses_injected_cover_letter_generator(seeded_store, identity_id, job_url):
    pkg = generate_application_for_job(
        seeded_store, identity_id, job_url, cover_letter_generator=FakeGen()
    )
    assert pkg is not None and pkg.cover_letter == "INJECTED"
```

(Read `packages/careeros-job-search/tests/` first and reuse its existing seeding fixtures rather than hand-rolling.)

- [ ] **Step 2: Run → FAIL** (unexpected keyword arg).

- [ ] **Step 3: Implement** — add the param and pass it through:

```python
def generate_application_for_job(
    store,
    identity_id,
    job_url,
    *,
    provider_registry=None,
    cover_letter_generator=None,
):
    ...
    return build_application_package(brain, posting, cover_letter_generator=cover_letter_generator)
```

Add `from careeros_application_engine import CoverLetterGenerator` for the type hint (import already present for `build_application_package`).

- [ ] **Step 4: Run → PASS.** ruff check + format.

- [ ] **Step 5: Commit** — `git commit -am "feat(ai): inject cover-letter generator through generate_application_for_job"`

---

### Task 4: API AI support (cipher, vault, key resolution)

**Files:**
- Create: `packages/careeros-api/src/careeros_api/ai_support.py`
- Modify: `packages/careeros-api/pyproject.toml` (add deps `careeros-ai`, `careeros-credentials`, `careeros-application-engine` + workspace sources)
- Test: `packages/careeros-api/tests/test_ai_support.py`

**Interfaces:**
- Produces:
  - `store_workspace_key(store, workspace_id: str, api_key: str) -> None`
  - `delete_workspace_key(store, workspace_id: str) -> None`
  - `has_workspace_key(store, workspace_id: str) -> bool`
  - `resolve_cover_letter_generator(store, workspace_id: str) -> CoverLetterGenerator | None` (AI if key present & `CAREEROS_SECRET_KEY`/dev key decrypts it, else `None`)
  - `ai_model() -> str`

- [ ] **Step 1: Write failing test**

```python
import os
from careeros_common import open_store
from careeros_api.ai_support import (
    store_workspace_key,
    has_workspace_key,
    delete_workspace_key,
    resolve_cover_letter_generator,
)
from careeros_application_engine import AICoverLetterGenerator


def test_key_round_trip_and_generator_selection(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    assert has_workspace_key(store, "ws1") is False
    assert resolve_cover_letter_generator(store, "ws1") is None
    store_workspace_key(store, "ws1", "sk-ant-abc")
    assert has_workspace_key(store, "ws1") is True
    gen = resolve_cover_letter_generator(store, "ws1")
    assert isinstance(gen, AICoverLetterGenerator)
    delete_workspace_key(store, "ws1")
    assert has_workspace_key(store, "ws1") is False
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement `ai_support.py`**

```python
"""First-party wrapper over CredentialVault for the workspace's Anthropic
key, plus generator resolution. The app is authorized explicitly (it is
not a third-party plugin)."""

from __future__ import annotations
import base64
import hashlib
import os
from careeros_ai import AnthropicClient, DEFAULT_MODEL
from careeros_application_engine import AICoverLetterGenerator, CoverLetterGenerator
from careeros_credentials import (
    CredentialAuditLog,
    CredentialVault,
    SecretCipher,
    SecretNotFoundError,
    credential_permission,
)

_SERVICE = "anthropic_api_key"
_REQUESTER = "careeros-app"


def _cipher() -> SecretCipher:
    key = os.environ.get("CAREEROS_SECRET_KEY")
    if not key:  # deterministic dev/test fallback; prod always sets the env
        key = base64.urlsafe_b64encode(hashlib.sha256(b"careeros-dev-secret").digest()).decode()
    return SecretCipher(key)


def _vault(store) -> CredentialVault:
    lookup = lambda _requester: frozenset({credential_permission(_SERVICE)})
    return CredentialVault(store, _cipher(), CredentialAuditLog(store), lookup_permissions=lookup)


def ai_model() -> str:
    return os.environ.get("CAREEROS_AI_MODEL", DEFAULT_MODEL)


def store_workspace_key(store, workspace_id: str, api_key: str) -> None:
    _vault(store).store_secret(workspace_id, _SERVICE, api_key, requester_id=_REQUESTER)


def delete_workspace_key(store, workspace_id: str) -> None:
    _vault(store).delete_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)


def has_workspace_key(store, workspace_id: str) -> bool:
    return _vault(store).has_secret(workspace_id, _SERVICE)


def _get_key(store, workspace_id: str) -> str | None:
    try:
        return _vault(store).get_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)
    except SecretNotFoundError:
        return None


def resolve_cover_letter_generator(store, workspace_id: str) -> CoverLetterGenerator | None:
    key = _get_key(store, workspace_id)
    if not key:
        return None
    return AICoverLetterGenerator(AnthropicClient(key, ai_model()))
```

- [ ] **Step 4: Add deps** in `packages/careeros-api/pyproject.toml`: add `"careeros-ai"`, `"careeros-credentials"`, `"careeros-application-engine"` to `dependencies` and the matching `{ workspace = true }` sources. `uv lock && uv sync --all-packages`.

- [ ] **Step 5: Run → PASS.** ruff check + format.

- [ ] **Step 6: Commit** — `git commit -am "feat(ai): API key vault wrapper + generator resolution"`

---

### Task 5: Settings router (`/settings/ai`)

**Files:**
- Create: `packages/careeros-api/src/careeros_api/routers/settings.py`
- Modify: `packages/careeros-api/src/careeros_api/__init__.py` (register the router — find where other routers are `include_router`ed)
- Modify: `packages/careeros-api/src/careeros_api/schemas.py` (add request/response models)
- Test: `packages/careeros-api/tests/test_settings_api.py`

**Interfaces:**
- Consumes: `ai_support` (Task 4); `Context`, `Permission.CAREER_BRAIN_WRITE`.
- Produces: `GET/PUT/DELETE /settings/ai`.

- [ ] **Step 1: Write failing test**

```python
def test_ai_key_round_trip(client, auth_headers):
    h = auth_headers()
    assert client.get("/settings/ai", headers=h).json()["has_key"] is False
    assert (
        client.put("/settings/ai", headers=h, json={"api_key": "sk-ant-abc123"}).status_code == 200
    )
    assert client.get("/settings/ai", headers=h).json()["has_key"] is True
    assert client.delete("/settings/ai", headers=h).status_code == 200
    assert client.get("/settings/ai", headers=h).json()["has_key"] is False


def test_put_rejects_malformed_key(client, auth_headers):
    assert (
        client.put("/settings/ai", headers=auth_headers(), json={"api_key": "nope"}).status_code
        == 422
    )


def test_settings_requires_auth(client):
    assert client.get("/settings/ai").status_code == 401
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Add schemas** in `schemas.py`:

```python
class AiKeyRequest(BaseModel):
    api_key: str


class AiStatusResponse(BaseModel):
    has_key: bool
    model: str
```

- [ ] **Step 4: Implement `settings.py`**

```python
"""Workspace settings: the Anthropic API key powering AI features. The key
is write-only over the API — GET returns only whether one is set."""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_api.schemas import AiKeyRequest, AiStatusResponse
from careeros_tenancy import Permission

router = APIRouter(tags=["settings"])


@router.get("/settings/ai", response_model=AiStatusResponse)
def get_ai(context: Context) -> AiStatusResponse:
    return AiStatusResponse(
        has_key=ai_support.has_workspace_key(context.store, context.account.workspace_id),
        model=ai_support.ai_model(),
    )


@router.put("/settings/ai", response_model=AiStatusResponse)
def put_ai(body: AiKeyRequest, context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    key = body.api_key.strip()
    if not key.startswith("sk-ant-") or len(key) < 20:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "that doesn't look like an Anthropic API key (expected 'sk-ant-…')",
        )
    ai_support.store_workspace_key(context.store, context.account.workspace_id, key)
    return AiStatusResponse(has_key=True, model=ai_support.ai_model())


@router.delete("/settings/ai", response_model=AiStatusResponse)
def delete_ai(context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    ai_support.delete_workspace_key(context.store, context.account.workspace_id)
    return AiStatusResponse(has_key=False, model=ai_support.ai_model())
```

- [ ] **Step 5: Register router** in `careeros_api/__init__.py` next to the others: `from careeros_api.routers import settings` and `app.include_router(settings.router)`.

- [ ] **Step 6: Run → PASS.** ruff check + format.

- [ ] **Step 7: Commit** — `git commit -am "feat(ai): settings router for the Anthropic key (write-only)"`

---

### Task 6: Inject AI into `/opportunities/generate` + `ai_used`

**Files:**
- Modify: `packages/careeros-api/src/careeros_api/routers/opportunities.py`
- Modify: `packages/careeros-api/src/careeros_api/schemas.py` (`ApplicationPackageResponse` gains `ai_used: bool`)
- Test: `packages/careeros-api/tests/test_opportunities_api.py` (extend)

**Interfaces:**
- Consumes: `ai_support.resolve_cover_letter_generator`, `generate_application_for_job(..., cover_letter_generator=...)`.

- [ ] **Step 1: Write failing tests** — with no key, `generate` response has `ai_used == False`; with a monkeypatched `resolve_cover_letter_generator` returning a fake generator (`.generate` → "AI!"), response `ai_used == True` and `cover_letter == "AI!"`; when the fake generator raises, response falls back to template and `ai_used == False`. (Reuse the existing seeding in `test_opportunities_api.py`.)

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement** the endpoint:

```python
@router.post("/generate", response_model=ApplicationPackageResponse)
def generate(body: GenerateRequest, context: Context) -> ApplicationPackageResponse:
    workspace_id = context.account.workspace_id
    generator = ai_support.resolve_cover_letter_generator(context.store, workspace_id)
    ai_used = generator is not None
    try:
        package = generate_application_for_job(
            context.store, _identity_id(context), body.job_url, cover_letter_generator=generator
        )
    except AIError:
        package = generate_application_for_job(context.store, _identity_id(context), body.job_url)
        ai_used = False
    if package is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "that posting is no longer available to generate from"
        )
    return ApplicationPackageResponse(
        resume_text=package.resume_text, cover_letter=package.cover_letter, ai_used=ai_used
    )
```

Add imports: `from careeros_api import ai_support`, `from careeros_ai import AIError`. Add `ai_used: bool = False` to `ApplicationPackageResponse`.

- [ ] **Step 4: Run → PASS.** Full API suite: `uv run pytest packages/careeros-api -q`. ruff check + format.

- [ ] **Step 5: Commit** — `git commit -am "feat(ai): real-AI cover letters on /opportunities/generate with template fallback"`

---

### Task 7: Web — Settings page + key form + nav

**Files:**
- Modify: `web/lib/api.ts` (types + methods)
- Create: `web/app/api/settings/ai/route.ts` (GET/PUT/DELETE forwarders)
- Create: `web/app/settings/page.tsx`
- Create: `web/components/settings/AiKeyForm.tsx`
- Modify: `web/components/Shell.tsx` (add Settings nav link)

**Interfaces:**
- Consumes: `/settings/ai` API (Task 5).

- [ ] **Step 1: Extend `api.ts`** — add to the `api` object and types:

```ts
export type AiStatus = { has_key: boolean; model: string };
// in api:
aiStatus: (token: string) => request<AiStatus>("/settings/ai", { token }),
setAiKey: (token: string, api_key: string) =>
  request<AiStatus>("/settings/ai", { token, method: "PUT", body: { api_key } }),
deleteAiKey: (token: string) => request<AiStatus>("/settings/ai", { token, method: "DELETE" }),
```

Also add `ai_used?: boolean` to the generate result type used by the opportunities client method.

- [ ] **Step 2: Route handler** `web/app/api/settings/ai/route.ts` — GET/PUT/DELETE reading the cookie token (mirror `web/app/api/opportunities/generate/route.ts`), calling `api.aiStatus/setAiKey/deleteAiKey`, mapping `ApiError.status`.

- [ ] **Step 3: `AiKeyForm.tsx`** (client) — password field + Save (PUT) + Remove (DELETE); shows "AI is ON — model X" when `has_key`, else "AI is off — using free templates"; `router.refresh()` after change; inline error text. Follow the `ResumeUpload.tsx` fetch-to-route pattern.

- [ ] **Step 4: `settings/page.tsx`** (server) — `requireAccount()`, `const status = await api.aiStatus(token)`, render inside `<Shell>` with `<AiKeyForm initial={status} />` and a short help line linking to console.anthropic.com. `export const dynamic = "force-dynamic"`.

- [ ] **Step 5: Nav** — add `{ href: "/settings", label: "Settings" }` to the nav list in `Shell.tsx` (match existing structure).

- [ ] **Step 6: Typecheck** — `cd web && npx --no-install tsc --noEmit` → exit 0.

- [ ] **Step 7: Commit** — `git commit -am "feat(ai): Settings page to manage the Anthropic key"`

---

### Task 8: Web badge + config + docs

**Files:**
- Modify: the opportunities generate result component (find with `grep -rn "cover_letter\|generatePackage\|Generate" web/components web/app/opportunities`)
- Modify: `render.yaml`
- Modify: `docs/development/go-live-runbook.md`

- [ ] **Step 1: `ai_used` badge** — where the generated cover letter renders, show `✨ AI-written` when `ai_used`, else `Template`. Typecheck.

- [ ] **Step 2: `render.yaml`** — under `careeros-api` `envVars` add:

```yaml
      - key: CAREEROS_SECRET_KEY
        generateValue: true
      - key: CAREEROS_AI_MODEL
        sync: false
```

- [ ] **Step 3: Runbook note** — add a short "AI features" subsection: users add their own Anthropic key in Settings; `CAREEROS_SECRET_KEY` is auto-generated by Render and **must stay stable** (rotating it makes stored keys undecryptable).

- [ ] **Step 4: Full verification** — `uv run pytest -q` (expect prior total + new tests, all pass); `uv run ruff check . && uv run ruff format --check .`; `cd web && npx --no-install tsc --noEmit`.

- [ ] **Step 5: Commit** — `git commit -am "feat(ai): AI-written badge, render secret key, runbook"`

---

## Self-Review

- **Spec coverage:** careeros-ai (T1), AICoverLetterGenerator+guardrail (T2), injectable seam (T3), encrypted key storage via vault + `CAREEROS_SECRET_KEY` (T4), settings endpoints write-only (T5), generate injection + `ai_used` + AI-failure fallback (T6), Settings page + nav + route handler (T7), badge + render.yaml + runbook (T8). All spec sections map to a task.
- **Placeholder scan:** none — every code step carries real content; T3 test reuses existing fixtures (explicitly instructed to read them first) rather than a vague "similar to".
- **Type consistency:** `complete(*, system, prompt) -> str`, `resolve_cover_letter_generator -> CoverLetterGenerator | None`, `AiStatusResponse{has_key, model}`, `ApplicationPackageResponse.ai_used` used consistently across tasks.
