"""OpenAICompatibleClient: one client for every provider that speaks the
OpenAI Chat Completions API — OpenRouter and OpenAI both do. Same AIClient
seam as AnthropicClient (strings in, strings out)."""

from __future__ import annotations

import httpx

from careeros_ai.client import AIAuthError, AIUnavailableError, default_timeout


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._http = http_client or httpx.Client(timeout=default_timeout())

    def complete(self, *, system: str, prompt: str) -> str:
        try:
            response = self._http.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "content-type": "application/json",
                },
                json={
                    "model": self._model,
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
        except httpx.HTTPError as error:
            raise AIUnavailableError(str(error)) from error
        if response.status_code in (401, 403):
            raise AIAuthError("the provider rejected the API key")
        if response.status_code == 429 or response.status_code >= 500:
            raise AIUnavailableError(f"provider returned {response.status_code}")
        if response.status_code >= 400:
            raise AIUnavailableError(
                f"provider returned {response.status_code}: {response.text[:200]}"
            )
        choices = response.json().get("choices", [])
        if not choices:
            return ""
        return (choices[0].get("message", {}).get("content") or "").strip()
