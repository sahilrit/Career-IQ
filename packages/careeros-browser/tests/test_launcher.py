"""Tests for the launcher module's import-safety guarantee.

Neither playwright's nor camoufox's actual browser binaries are ever
required just to *import* this module — only to call the launch
functions. Both real launches need a browser binary, so they're
exercised only via dependency injection elsewhere (``check_browser_health``
and friends), never here.
"""

from __future__ import annotations

import sys

import pytest

from careeros_browser import BrowserError, launch_browser_session, launch_camoufox_session


def test_launch_camoufox_session_is_importable_regardless_of_camoufox_being_installed():
    # Importing careeros_browser must never fail just because the optional
    # camoufox extra isn't installed — the import inside
    # launch_camoufox_session is deferred to call time for exactly this
    # reason, whether or not camoufox actually happens to be present here.
    assert callable(launch_camoufox_session)


def test_launch_camoufox_session_raises_a_clear_error_without_camoufox(monkeypatch):
    # Force the "not installed" path regardless of whether camoufox is
    # actually present in this environment: setting a module to None in
    # sys.modules makes Python's import machinery raise ImportError for it,
    # exactly as if the package were missing.
    monkeypatch.setitem(sys.modules, "camoufox.sync_api", None)
    monkeypatch.setitem(sys.modules, "camoufox", None)

    with pytest.raises(BrowserError, match="camoufox"), launch_camoufox_session():
        pass  # pragma: no cover - never reached; import fails first


def test_launch_browser_session_is_still_importable():
    assert callable(launch_browser_session)
