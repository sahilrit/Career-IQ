"""Browser automation exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class BrowserError(CareerOSError):
    """Base class for all browser automation errors."""


class SelectorTimeoutError(BrowserError):
    """Raised when waiting for a selector exceeds its timeout."""


class DownloadError(BrowserError):
    """Raised when an expected download never materializes."""
