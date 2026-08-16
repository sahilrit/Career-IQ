"""Import a Career Brain from an uploaded resume PDF.

Heuristic, dependency-light (pypdf only, no LLM): it extracts the name,
email, phone, a professional summary, and a skills list from the resume
text and seeds a Career Brain. It's a starting point — the user refines
everything on the Career Brain page — so it errs toward capturing more
and never fabricates content it can't find.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

from careeros_career_brain import CareerBrain, CareerBrainRepository
from careeros_career_brain.models import Identity, Skill
from careeros_common import DocumentStore

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
_SKILLS_HEADING_RE = re.compile(
    r"(core competencies|skills|technical skills|areas of expertise|expertise)\s*:?\s*$",
    re.IGNORECASE,
)
_SECTION_HEADING_RE = re.compile(
    r"^(professional summary|summary|profile|about|objective)\s*:?\s*$", re.IGNORECASE
)
_NEXT_SECTION_RE = re.compile(
    r"^(experience|employment|professional experience|education|projects|work history|"
    r"core competencies|skills|certifications)\s*:?\s*$",
    re.IGNORECASE,
)
# Split a skills blob on commas, pipes, and bullets (not slashes — keep
# "A/B Testing", "UX/UI" intact).
_SKILL_SPLIT_RE = re.compile(r"[,|•·]|\s{2,}")
_CATEGORY_LABEL_RE = re.compile(r"^[A-Za-z0-9 &/-]{3,40}:\s*")


@dataclass
class ParsedResume:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    headline: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)


def extract_text_from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _looks_like_name(line: str) -> bool:
    words = line.split()
    return 1 < len(words) <= 5 and all(w[:1].isalpha() for w in words) and "@" not in line


def parse_resume(text: str) -> ParsedResume:
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    parsed = ParsedResume()

    email_match = _EMAIL_RE.search(text)
    if email_match:
        parsed.email = email_match.group(0)
    phone_match = _PHONE_RE.search(text)
    if phone_match:
        candidate = phone_match.group(1).strip()
        if sum(ch.isdigit() for ch in candidate) >= 8:
            parsed.phone = candidate

    # Name: the first plausible name-like line near the top.
    name_index: int | None = None
    for index, line in enumerate(non_empty[:5]):
        if _looks_like_name(line):
            parsed.full_name = line.title() if line.isupper() else line
            name_index = index
            break
    # Headline: the line right after the name, if it's short and not contact info.
    if name_index is not None and name_index + 1 < len(non_empty):
        candidate = non_empty[name_index + 1]
        if "@" not in candidate and not _PHONE_RE.search(candidate) and len(candidate) < 120:
            parsed.headline = candidate

    parsed.summary = _extract_section(lines, _SECTION_HEADING_RE)
    parsed.skills = _extract_skills(lines)
    return parsed


def _extract_section(lines: list[str], heading_re: re.Pattern[str]) -> str:
    collected: list[str] = []
    capturing = False
    for line in lines:
        if heading_re.match(line):
            capturing = True
            continue
        if capturing:
            if not line:
                if collected:
                    break
                continue
            if _NEXT_SECTION_RE.match(line):
                break
            collected.append(line)
    return " ".join(collected).strip()


def _extract_skills(lines: list[str]) -> list[str]:
    blob: list[str] = []
    capturing = False
    for line in lines:
        if _SKILLS_HEADING_RE.match(line):
            capturing = True
            continue
        if capturing:
            if _NEXT_SECTION_RE.match(line) and not _SKILLS_HEADING_RE.match(line):
                break
            if not line and blob:
                break
            if line:
                # Drop a leading "Paid Media:" style category label.
                blob.append(_CATEGORY_LABEL_RE.sub("", line))

    skills: list[str] = []
    seen: set[str] = set()
    for part in _SKILL_SPLIT_RE.split(", ".join(blob)):
        name = part.strip(" .-•·")
        if 2 <= len(name) <= 40 and name.lower() not in seen:
            seen.add(name.lower())
            skills.append(name)
    return skills[:40]


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
