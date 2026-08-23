"""Heuristic resume parsing — turn an uploaded resume PDF into structured
fields (name, email, phone, headline, summary, skills) with no LLM.

This lives in the Career Brain package (not a UI package) so every
front end — the Streamlit dashboard and the FastAPI/React app — seeds a
brain from the same, tested logic. It errs toward capturing more and
never fabricates content it can't find; the user refines the rest.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import date

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

_EXPERIENCE_HEADING_RE = re.compile(
    r"^(experience|employment|professional experience|work experience|work history"
    r"|career history)\s*:?\s*$",
    re.IGNORECASE,
)
# Section headings that end the experience block.
_AFTER_EXPERIENCE_RE = re.compile(
    r"^(education|projects|certifications|skills|core competencies|technical skills"
    r"|awards|publications|references|languages|volunteer|interests)\s*:?\s*$",
    re.IGNORECASE,
)
_EDUCATION_HEADING_RE = re.compile(r"^education\s*:?\s*$", re.IGNORECASE)
_CERT_HEADING_RE = re.compile(
    r"^(certifications?|licenses?(?:\s*(?:&|and)\s*certifications?)?)\s*:?\s*$", re.IGNORECASE
)
# Any known section heading — used to bound a section we're reading.
_ANY_HEADING_RE = re.compile(
    r"^(professional experience|experience|employment|work experience|work history"
    r"|career history|education|certifications?|licenses?.*|projects|skills"
    r"|core competencies|technical skills|areas of expertise|expertise|awards|honors"
    r"|publications|languages|volunteer|interests|professional summary|summary|profile"
    r"|about|objective|references)\s*:?\s*$",
    re.IGNORECASE,
)
_MONTHS = {
    m: i
    for i, name in enumerate(
        [
            "jan|january",
            "feb|february",
            "mar|march",
            "apr|april",
            "may",
            "jun|june",
            "jul|july",
            "aug|august",
            "sep|sept|september",
            "oct|october",
            "nov|november",
            "dec|december",
        ],
        start=1,
    )
    for m in name.split("|")
}
_PRESENT_RE = re.compile(r"present|current|now|ongoing|to date", re.IGNORECASE)
# One date token: an optional *real* month name then a 4-digit year. Restricting
# to month names stops a company word ("Acme 2020") being read as a month.
_MON_NAMES = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_DATE_TOKEN = rf"(?:({_MON_NAMES})\.?\s+)?((?:19|20)\d{{2}})"
_SEP = "[-\u2013\u2014]"  # hyphen, en dash, em dash
_END = "(present|current|now|ongoing|to date)"
_DATE_RANGE_RE = re.compile(
    rf"{_DATE_TOKEN}\s*(?:{_SEP}|to|until)\s*(?:{_DATE_TOKEN}|{_END})",
    re.IGNORECASE,
)
# Separators between a title and a company on one line.
_TITLE_COMPANY_SPLIT = re.compile(
    "(?:\\s*,\\s+|\\s+(?:[-\\u2013\\u2014|\u00b7\u2022@]|\\bat\\b)\\s+)", re.IGNORECASE
)


@dataclass
class ParsedExperience:
    title: str
    company: str
    start_date: date
    end_date: date | None = None
    description: str = ""


@dataclass
class ParsedEducation:
    institution: str
    credential: str
    end_date: date | None = None


@dataclass
class ParsedCertification:
    name: str
    issuer: str | None = None


@dataclass
class ParsedResume:
    full_name: str = ""
    email: str = ""
    phone: str = ""
    headline: str = ""
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experiences: list[ParsedExperience] = field(default_factory=list)
    education: list[ParsedEducation] = field(default_factory=list)
    certifications: list[ParsedCertification] = field(default_factory=list)


def extract_text_from_pdf(data: bytes) -> str:
    # pypdf imported lazily so the domain package stays import-light; the
    # dependency is declared by the callers that actually parse PDFs.
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _looks_like_name(line: str) -> bool:
    words = line.split()
    return 1 < len(words) <= 5 and all(w[:1].isalpha() for w in words) and "@" not in line


_MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _normalize_numeric_dates(text: str) -> str:
    """Rewrite "05/2024" / "05-2024" to "May 2024" so numeric résumé dates flow
    through the same month-name logic."""

    def repl(match: re.Match[str]) -> str:
        month = int(match.group(1))
        return f"{_MONTH_ABBR[month - 1]} {match.group(2)}"

    return re.sub(r"\b(0?[1-9]|1[0-2])[/.]((?:19|20)\d{2})\b", repl, text)


def parse_resume(text: str) -> ParsedResume:
    text = _normalize_numeric_dates(text)
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
    parsed.experiences = _extract_experiences(non_empty)
    parsed.education = _extract_education(non_empty)
    parsed.certifications = _extract_certifications(non_empty)
    return parsed


def _section_lines(non_empty: list[str], heading_re: re.Pattern[str]) -> list[str]:
    """Lines under a heading, up to the next known section heading."""
    out: list[str] = []
    capturing = False
    for line in non_empty:
        if heading_re.match(line):
            capturing = True
            continue
        if capturing:
            if _ANY_HEADING_RE.match(line):
                break
            out.append(line)
    return out


def parse_resume_pdf(data: bytes) -> ParsedResume:
    """Convenience: extract text from a PDF and parse it in one call."""
    return parse_resume(extract_text_from_pdf(data))


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


def _to_date(month: str | None, year: str) -> date:
    return date(int(year), _MONTHS.get((month or "").lower(), 1), 1)


def _split_title_company(text: str) -> tuple[str, str]:
    cleaned = text.strip(" ,|-\u2013\u2014\u2022\u00b7\t")
    if not cleaned:
        return "", ""
    parts = _TITLE_COMPANY_SPLIT.split(cleaned, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return cleaned, ""


# Bullet glyphs (incl. the \x7f pypdf sometimes emits) — lines that describe
# achievements, never a role header.
_BULLET_CHARS = "\x7f\uf0b7\u2022\u00b7\u25aa\u2023*"


def _is_bullet(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped[0] in _BULLET_CHARS


def _title_from_above(block: list[str], index: int) -> str:
    """The role title in a 'Title\\nCompany | Dates | Location' layout sits on
    the line above the date line. Look back a few lines, skipping bullets and
    other date lines."""
    for j in range(index - 1, max(-1, index - 4), -1):
        candidate = block[j].strip()
        if not candidate or _is_bullet(candidate) or _DATE_RANGE_RE.search(candidate):
            continue
        if len(candidate) > 90:
            continue
        return candidate.split("|")[0].strip()
    return ""


def _extract_experiences(non_empty: list[str]) -> list[ParsedExperience]:
    """Best-effort: within the experience section, each line carrying a date
    range is one role. Handles both common layouts — "Company | Dates |
    Location" with the title on the line above, and an inline "Title — Company
    Dates" line. Résumé layouts vary, so this is meant to be reviewed, not
    trusted blindly; it never invents a role it can't anchor to a date."""
    # Isolate the experience block.
    block: list[str] = []
    capturing = False
    for line in non_empty:
        if _EXPERIENCE_HEADING_RE.match(line):
            capturing = True
            continue
        if capturing:
            if _AFTER_EXPERIENCE_RE.match(line):
                break
            block.append(line)

    # Each non-bullet line with a date range anchors a role.
    anchors = [
        i for i, line in enumerate(block) if not _is_bullet(line) and _DATE_RANGE_RE.search(line)
    ]
    experiences: list[ParsedExperience] = []
    seen: set[tuple[str, str]] = set()
    for k, index in enumerate(anchors):
        line = block[index]
        match = _DATE_RANGE_RE.search(line)
        start = _to_date(match.group(1), match.group(2))
        end = None if match.group(5) else _to_date(match.group(3), match.group(4))

        before = line[: match.start()].strip(" |\t")
        after = line[match.end() :].strip(" |\t")
        if "|" in line:
            company = (before or after).split("|")[0].strip()
            title = _title_from_above(block, index) or company
            if title == company:
                company = ""
        else:
            title, company = _split_title_company(f"{before} {after}".strip())
            if not title:
                title = _title_from_above(block, index)

        if not title or ";" in company or len(company) > 60 or len(title) > 80:
            continue
        key = (title.lower(), company.lower())
        if key in seen:
            continue
        seen.add(key)

        # Description = the bullet/continuation lines until the next role. The
        # next role's title sits just above its date line, so stop before it.
        next_anchor = anchors[k + 1] if k + 1 < len(anchors) else len(block)
        desc_end = next_anchor
        if next_anchor < len(block) and next_anchor - 1 > index:
            above = block[next_anchor - 1]
            if not _is_bullet(above) and not _DATE_RANGE_RE.search(above):
                desc_end = next_anchor - 1
        description = _clean_bullets(block[index + 1 : desc_end])

        experiences.append(
            ParsedExperience(
                title=title[:120],
                company=company[:120],
                start_date=start,
                end_date=end,
                description=description[:2000],
            )
        )
        if len(experiences) >= 15:
            break
    return experiences


def _clean_bullets(lines: list[str]) -> str:
    """Rebuild a role's bullet list: a new bullet starts on a bullet glyph;
    lines without one continue the previous bullet (wrapped text)."""
    bullets: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] in _BULLET_CHARS:
            bullets.append(stripped.lstrip(_BULLET_CHARS + " ").strip())
        elif bullets:
            bullets[-1] = f"{bullets[-1]} {stripped}".strip()
        else:
            bullets.append(stripped)
    return "\n".join(f"• {b}" for b in bullets if b)


def _extract_education(non_empty: list[str]) -> list[ParsedEducation]:
    """A year (with a "|" or on its own line) marks the institution line; the
    credential is the line above it."""
    block = _section_lines(non_empty, _EDUCATION_HEADING_RE)
    out: list[ParsedEducation] = []
    seen: set[tuple[str, str]] = set()
    for i, line in enumerate(block):
        if _is_bullet(line):
            continue
        year = re.search(r"(?:19|20)\d{2}", line)
        if not year:
            continue
        institution = line.split("|")[0].strip() if "|" in line else line[: year.start()].strip()
        credential = ""
        prev = block[i - 1] if i > 0 else ""
        if prev and not re.search(r"(?:19|20)\d{2}", prev) and not _is_bullet(prev):
            credential = prev.split("|")[0].strip()
        if not credential:
            credential, institution = institution, ""
        if not credential:
            continue
        key = (institution.lower(), credential.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(
            ParsedEducation(
                institution=institution[:120],
                credential=credential[:160],
                end_date=_to_date(None, year.group(0)),
            )
        )
    return out[:8]


def _extract_certifications(non_empty: list[str]) -> list[ParsedCertification]:
    """Each entry is usually "Name — Issuer" (bulleted or plain)."""
    block = _section_lines(non_empty, _CERT_HEADING_RE)
    out: list[ParsedCertification] = []
    seen: set[tuple[str, str]] = set()
    for line in block:
        text = line.strip().lstrip(_BULLET_CHARS + " ").strip()
        if len(text) < 2:
            continue
        name, issuer = _split_title_company(text)
        cert = ParsedCertification(name=name[:160], issuer=(issuer or None))
        key = (cert.name.lower(), (cert.issuer or "").lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(cert)
    return out[:15]
