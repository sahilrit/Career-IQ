"""Providers that can be switched off without a code change.

Most of our sources are public APIs that publish a feed and expect to be
read. A few read a site the way a browser would — LinkedIn is the first —
and those concentrate traffic on whichever IP runs the search. They stay
on by default so a fresh install searches everything, but an operator who
would rather not point them at a shared production IP can turn each one
off with a single environment variable.
"""

from __future__ import annotations

import os

LINKEDIN_ENV_VAR = "CAREEROS_ENABLE_LINKEDIN"

_FALSEY = {"0", "false", "no", "off", ""}


def _enabled(env_var: str) -> bool:
    raw = os.environ.get(env_var)
    if raw is None:
        return True
    return raw.strip().lower() not in _FALSEY


def linkedin_enabled() -> bool:
    """True unless ``CAREEROS_ENABLE_LINKEDIN`` is explicitly switched off."""
    return _enabled(LINKEDIN_ENV_VAR)
