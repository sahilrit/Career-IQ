"""AnthropicClient: a minimal Messages API caller over httpx (no SDK, to
keep the API image slim). One non-streaming completion per call."""

from __future__ import annotations

import httpx

from careeros_ai.client import DEFAULT_MODEL, AIAuthError, AIUnavailableError

_URL = "https://api.anthropic.com/v1/messages"
_VERSION = "2023-06-01"


class AnthropicClient:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        *,
        http_client: httpx.Client | None = None,
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
        if response.status_code == 429 or response.status_code >= 500:
            raise AIUnavailableError(f"Anthropic returned {response.status_code}")
        if response.status_code >= 400:
            raise AIUnavailableError(
                f"Anthropic returned {response.status_code}: {response.text[:200]}"
            )
        blocks = response.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
