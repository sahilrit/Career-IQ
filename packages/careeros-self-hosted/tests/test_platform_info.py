"""Tests for platform info."""

from __future__ import annotations

from careeros_self_hosted import collect_platform_info, is_os_supported


def test_darwin_linux_and_windows_are_supported():
    assert is_os_supported("Darwin") is True
    assert is_os_supported("Linux") is True
    assert is_os_supported("Windows") is True


def test_unknown_os_is_not_supported():
    assert is_os_supported("PlayStationOS") is False


def test_collect_platform_info_reflects_the_real_running_environment():
    info = collect_platform_info()
    assert info.python_version.startswith("3.")
    assert info.is_supported_os is True
