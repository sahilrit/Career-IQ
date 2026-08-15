"""Tests for run_health_checks / is_platform_ready."""

from __future__ import annotations

from careeros_self_hosted import is_platform_ready, run_health_checks


def test_run_health_checks_returns_one_result_per_check(tmp_path):
    results = run_health_checks(tmp_path)
    names = {result.check_name for result in results}
    assert names == {"data_dir_writable", "sqlite_store", "browser_automation", "dashboard_ui"}


def test_data_dir_writable_passes_for_a_real_temp_dir(tmp_path):
    results = run_health_checks(tmp_path)
    data_dir_result = next(r for r in results if r.check_name == "data_dir_writable")
    assert data_dir_result.passed is True


def test_sqlite_store_check_passes_for_a_real_temp_dir(tmp_path):
    results = run_health_checks(tmp_path)
    sqlite_result = next(r for r in results if r.check_name == "sqlite_store")
    assert sqlite_result.passed is True


def test_is_platform_ready_reflects_all_checks_passing(tmp_path):
    assert is_platform_ready(tmp_path) is True


def test_data_dir_writable_fails_when_path_is_actually_a_file(tmp_path):
    blocked = tmp_path / "not_a_directory"
    blocked.write_text("i am a file")
    results = run_health_checks(blocked)
    data_dir_result = next(r for r in results if r.check_name == "data_dir_writable")
    assert data_dir_result.passed is False
    assert data_dir_result.detail
