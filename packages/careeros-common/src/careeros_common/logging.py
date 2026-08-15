"""Structured logging setup shared by every CareerOS package.

Plain stdlib ``logging`` on purpose: no paid or hosted log provider is
required to run CareerOS. Downstream deployments can attach their own
handlers to the root logger (e.g. shipping to a self-hosted log stack)
without this module needing to know about them.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging(level: str = "INFO", *, json: bool = False) -> None:
    """Attach a single stdout handler to the root logger.

    Idempotent: only the first call configures anything, so packages and
    apps can each call this defensively during their own startup without
    producing duplicate log lines.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    if json:
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.addHandler(handler)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring root logging with defaults if needed."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
