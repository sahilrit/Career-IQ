"""Tests for SecretCipher."""

from __future__ import annotations

import pytest

from careeros_credentials import DecryptionError, SecretCipher


def test_encrypt_then_decrypt_roundtrips():
    cipher = SecretCipher(SecretCipher.generate_key())
    ciphertext = cipher.encrypt("super-secret-api-key")
    assert cipher.decrypt(ciphertext) == "super-secret-api-key"


def test_ciphertext_does_not_contain_the_plaintext():
    cipher = SecretCipher(SecretCipher.generate_key())
    ciphertext = cipher.encrypt("super-secret-api-key")
    assert "super-secret-api-key" not in ciphertext


def test_generate_key_produces_a_usable_key():
    key = SecretCipher.generate_key()
    assert isinstance(key, str)
    SecretCipher(key)  # must not raise


def test_decrypting_with_the_wrong_key_raises():
    cipher_a = SecretCipher(SecretCipher.generate_key())
    cipher_b = SecretCipher(SecretCipher.generate_key())
    ciphertext = cipher_a.encrypt("secret")
    with pytest.raises(DecryptionError):
        cipher_b.decrypt(ciphertext)


def test_decrypting_garbage_raises():
    cipher = SecretCipher(SecretCipher.generate_key())
    with pytest.raises(DecryptionError):
        cipher.decrypt("not-valid-ciphertext")
