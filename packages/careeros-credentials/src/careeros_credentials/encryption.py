"""SecretCipher: local, symmetric encryption for secrets at rest.

Uses ``cryptography``'s Fernet (open-source, free, well-audited) — no
paid key-management service required. The key itself should come from
an environment variable or local file the operator controls (never
hardcoded, never committed); ``SecretCipher.generate_key()`` is provided
for local/self-hosted setup.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from careeros_credentials.exceptions import DecryptionError


class SecretCipher:
    def __init__(self, key: bytes | str) -> None:
        if isinstance(key, str):
            key = key.encode("utf-8")
        self._fernet = Fernet(key)

    @staticmethod
    def generate_key() -> str:
        """A fresh key, suitable for e.g. CAREEROS_SECRET_KEY. Store it outside git."""
        return Fernet.generate_key().decode("utf-8")

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise DecryptionError(
                "Failed to decrypt secret: invalid key or corrupted data"
            ) from exc
