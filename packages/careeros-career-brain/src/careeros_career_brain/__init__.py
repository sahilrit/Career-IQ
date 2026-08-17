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
    Award,
    Certification,
    Company,
    Education,
    Experience,
    Goal,
    Identity,
    Language,
    Preferences,
    Project,
    Recruiter,
    Skill,
    StatusChange,
)
from careeros_career_brain.repository import CareerBrainRepository
from careeros_career_brain.resume_parsing import (
    ParsedResume,
    extract_text_from_pdf,
    parse_resume,
    parse_resume_pdf,
)

__all__ = [
    "ALLOWED_STATUS_TRANSITIONS",
    "Achievement",
    "Application",
    "ApplicationStatus",
    "Award",
    "CareerBrain",
    "CareerBrainError",
    "CareerBrainRepository",
    "Certification",
    "Company",
    "Education",
    "Experience",
    "Goal",
    "Identity",
    "InvalidStatusTransitionError",
    "Language",
    "ParsedResume",
    "Preferences",
    "Project",
    "Recruiter",
    "Skill",
    "StatusChange",
    "extract_text_from_pdf",
    "parse_resume",
    "parse_resume_pdf",
]
