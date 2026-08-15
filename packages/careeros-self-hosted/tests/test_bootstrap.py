"""Tests for ensure_data_dir."""

from __future__ import annotations

from careeros_self_hosted import ensure_data_dir


def test_creates_the_directory_if_missing(tmp_path):
    target = tmp_path / "nested" / "data"
    result = ensure_data_dir(target)
    assert result == target
    assert target.is_dir()


def test_is_idempotent_when_the_directory_already_exists(tmp_path):
    target = tmp_path / "data"
    ensure_data_dir(target)
    ensure_data_dir(target)
    assert target.is_dir()
