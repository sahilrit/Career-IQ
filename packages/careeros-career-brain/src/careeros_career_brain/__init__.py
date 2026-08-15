"""careeros_career_brain: the authoritative source of truth for a user's
professional identity. AI does not invent the user's career — Career
Brain is the record everything else is generated from.
"""

from careeros_career_brain.brain import CareerBrain
from careeros_career_brain.exceptions import CareerBrainError, InvalidStatusTransitionError
from careeros_career_brain.models import (
    ALLOWED_STATUS_TRANSITIONS,
    Achievement,
    Application,
    ApplicationStatus,
    Company,
    Experience,
    Goal,
    Identity,
    Preferences,
    Project,
    Recruiter,
    Skill,
    StatusChange,
)
from careeros_career_brain.repository import CareerBrainRepository

__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "Achievement",
    "Application",
    "ApplicationStatus",
    "CareerBrain",
    "CareerBrainError",
    "CareerBrainRepository",
    "Company",
    "Experience",
    "Goal",
    "Identity",
    "InvalidStatusTransitionError",
    "Preferences",
    "Project",
    "Recruiter",
    "Skill",
    "StatusChange",
]
