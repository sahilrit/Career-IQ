"""Resume content selection and rendering.

Selects which Career Brain content to feature for a specific opportunity
(via careeros_career_brain_engine's profile matching) and renders it to
plain text, Markdown, and simple HTML — no paid template service, no PDF
library dependency. Every word comes from Career Brain; nothing here
invents experience.
"""

from __future__ import annotations

import html as _html
from dataclasses import dataclass, field

from careeros_career_brain import Achievement, CareerBrain, Experience
from careeros_career_brain_engine import ProfileMatch, match_profile_to_posting
from careeros_job_providers import JobPosting


@dataclass
class ResumeContent:
    full_name: str
    headline: str
    email: str
    phone: str | None
    location: str | None
    links: dict[str, str] = field(default_factory=dict)
    summary: str = ""
    experiences: list[Experience] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)


def build_resume_content(brain: CareerBrain, posting: JobPosting) -> ResumeContent:
    match = match_profile_to_posting(brain, posting)
    ordered_experiences = sorted(brain.experiences, key=lambda e: e.start_date, reverse=True)
    return ResumeContent(
        full_name=brain.identity.full_name,
        headline=brain.identity.headline,
        email=brain.identity.email,
        phone=brain.identity.phone,
        location=brain.identity.location,
        links=dict(brain.identity.links),
        summary=_build_summary(brain, match),
        experiences=ordered_experiences,
        skills=[skill.name for skill in brain.skills],
    )


def _build_summary(brain: CareerBrain, match: ProfileMatch) -> str:
    parts = [brain.identity.headline] if brain.identity.headline else []
    # match.skill_match.matched_skills echoes the posting's own (often
    # lowercase) tag text; resolve back to the user's own skill casing
    # rather than quoting the posting verbatim in their resume.
    matched_lower = {name.lower() for name in match.skill_match.matched_skills}
    properly_cased = [skill.name for skill in brain.skills if skill.name.lower() in matched_lower]
    if properly_cased:
        parts.append("Skilled in " + ", ".join(properly_cased) + ".")
    return " ".join(parts)


def _achievement_bullet(achievement: Achievement) -> str:
    bullet = achievement.description
    if achievement.metric:
        bullet += f" ({achievement.metric})"
    return bullet


def render_resume_text(content: ResumeContent) -> str:
    lines = [content.full_name]
    if content.headline:
        lines.append(content.headline)
    contact = " | ".join(filter(None, [content.email, content.phone, content.location]))
    if contact:
        lines.append(contact)
    lines.append("")

    if content.summary:
        lines += ["SUMMARY", content.summary, ""]
    if content.skills:
        lines += ["SKILLS", ", ".join(content.skills), ""]

    lines.append("EXPERIENCE")
    for exp in content.experiences:
        end = exp.end_date.isoformat() if exp.end_date else "Present"
        lines.append(f"{exp.title} — {exp.company_name} ({exp.start_date.isoformat()} - {end})")
        if exp.description:
            lines.append(exp.description)
        for achievement in exp.achievements:
            lines.append(f"  - {_achievement_bullet(achievement)}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_resume_markdown(content: ResumeContent) -> str:
    lines = [f"# {content.full_name}"]
    if content.headline:
        lines.append(f"*{content.headline}*")
    contact = " | ".join(filter(None, [content.email, content.phone, content.location]))
    if contact:
        lines.append(contact)

    if content.summary:
        lines.append("\n## Summary\n" + content.summary)
    if content.skills:
        lines.append("\n## Skills\n" + ", ".join(content.skills))

    lines.append("\n## Experience")
    for exp in content.experiences:
        end = exp.end_date.isoformat() if exp.end_date else "Present"
        lines.append(f"\n### {exp.title} — {exp.company_name}")
        lines.append(f"_{exp.start_date.isoformat()} - {end}_")
        if exp.description:
            lines.append(exp.description)
        for achievement in exp.achievements:
            lines.append(f"- {_achievement_bullet(achievement)}")

    return "\n".join(lines).strip() + "\n"


def render_resume_html(content: ResumeContent) -> str:
    def esc(text: str) -> str:
        return _html.escape(text)

    parts = [f"<h1>{esc(content.full_name)}</h1>"]
    if content.headline:
        parts.append(f"<p><em>{esc(content.headline)}</em></p>")
    contact = " | ".join(filter(None, [content.email, content.phone, content.location]))
    if contact:
        parts.append(f"<p>{esc(contact)}</p>")

    if content.summary:
        parts.append(f"<h2>Summary</h2><p>{esc(content.summary)}</p>")
    if content.skills:
        parts.append(f"<h2>Skills</h2><p>{esc(', '.join(content.skills))}</p>")

    parts.append("<h2>Experience</h2>")
    for exp in content.experiences:
        end = exp.end_date.isoformat() if exp.end_date else "Present"
        parts.append(f"<h3>{esc(exp.title)} — {esc(exp.company_name)}</h3>")
        parts.append(f"<p><em>{esc(exp.start_date.isoformat())} - {esc(end)}</em></p>")
        if exp.description:
            parts.append(f"<p>{esc(exp.description)}</p>")
        if exp.achievements:
            items = "".join(f"<li>{esc(_achievement_bullet(a))}</li>" for a in exp.achievements)
            parts.append(f"<ul>{items}</ul>")

    return "\n".join(parts)
