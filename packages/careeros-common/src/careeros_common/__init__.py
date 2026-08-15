"""careeros_common: shared kernel utilities used by every CareerOS package.

Anything that more than one future package would otherwise duplicate
(configuration, logging, base exceptions) belongs here. Domain logic
(Career Brain, plugins, providers, ...) does not.
"""

from careeros_common.config import Settings, get_settings, reset_settings_cache
from careeros_common.exceptions import CareerOSError, ConfigurationError
from careeros_common.logging import configure_logging, get_logger
from careeros_common.storage import DocumentNotFoundError, DocumentStore

__all__ = [
    "CareerOSError",
    "ConfigurationError",
    "DocumentNotFoundError",
    "DocumentStore",
    "Settings",
    "configure_logging",
    "get_logger",
    "get_settings",
    "reset_settings_cache",
]
