"""AI Skill Marketplace exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class SkillMarketplaceError(CareerOSError):
    """Base class for all skill marketplace errors."""


class SkillNotFoundError(SkillMarketplaceError):
    """Raised when a skill id has no listing at all."""
