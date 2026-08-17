"""Seed a Career Brain from an uploaded resume PDF (Streamlit dashboard).

The parsing heuristics now live in `careeros_career_brain.resume_parsing`
so the API/React app shares the exact same logic. This module keeps the
dashboard-facing `import_resume` (persist a brand-new brain) and re-exports
the parser names for backward compatibility.
"""

from __future__ import annotations

from careeros_career_brain import (
    CareerBrain,
    CareerBrainRepository,
    ParsedResume,
    extract_text_from_pdf,
    parse_resume,
)
from careeros_career_brain.models import Identity, Skill
from careeros_common import DocumentStore

__all__ = [
    "ParsedResume",
    "extract_text_from_pdf",
    "import_resume",
    "parse_resume",
]


def import_resume(store: DocumentStore, data: bytes) -> tuple[CareerBrain, ParsedResume]:
    """Parse an uploaded resume PDF and seed a Career Brain from it."""
    parsed = parse_resume(extract_text_from_pdf(data))
    if not parsed.full_name and not parsed.email:
        raise ValueError("Couldn't read a name or email from that PDF — try another file.")

    brain = CareerBrain(
        identity=Identity(
            full_name=parsed.full_name or "Your Name",
            email=parsed.email or "you@example.com",
            phone=parsed.phone or None,
            headline=parsed.headline,
            summary=parsed.summary,
        ),
        skills=[Skill(name=name) for name in parsed.skills],
    )
    CareerBrainRepository(store).save(brain)
    return brain, parsed
