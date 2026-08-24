"""Tests for the launcher module's import-safety guarantee.

Neither playwright's nor camoufox's actual browser binaries are ever
required just to *import* this module — only to call the launch
functions. Both real launches need a browser binary this environment
does not have, so they're exercised only via dependency injection
elsewhere (``check_browser_health`` and friends), never here.
"""

from __future__ import annotations

import pytest

from careeros_browser import BrowserError, launch_browser_session, launch_camoufox_session


def test_launch_camoufox_session_is_importable_without_camoufox_installed():
    # The import above already proves this — camoufox is not installed in
    # this environment, and importing careeros_browser did not fail.
    assert callable(launch_camoufox_session)


def test_launch_camoufox_session_raises_a_clear_error_without_camoufox():
    with pytest.raises(BrowserError, match="camoufox"), launch_camoufox_session():
        pass  # pragma: no cover - never reached; camoufox isn't installed


def test_launch_browser_session_is_still_importable():
    assert callable(launch_browser_session)
