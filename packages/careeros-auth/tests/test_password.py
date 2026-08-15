"""Tests for stdlib PBKDF2 password hashing."""

from __future__ import annotations

from careeros_auth import hash_password, verify_password


def test_hash_then_verify_roundtrips():
    encoded = hash_password("Correct-Horse-Battery-1!")
    assert verify_password("Correct-Horse-Battery-1!", encoded)


def test_wrong_password_fails():
    encoded = hash_password("Correct-Horse-Battery-1!")
    assert not verify_password("wrong-password", encoded)


def test_same_password_hashes_differently_each_time():
    assert hash_password("Same-Password-1!") != hash_password("Same-Password-1!")


def test_iteration_count_is_embedded_per_hash():
    encoded = hash_password("Some-Password-1!", iterations=100_000)
    assert encoded.split("$")[1] == "100000"
    assert verify_password("Some-Password-1!", encoded)


def test_garbage_encoded_value_fails_instead_of_raising():
    assert not verify_password("anything", "not-a-real-hash")
    assert not verify_password("anything", "a$b$c$d")
