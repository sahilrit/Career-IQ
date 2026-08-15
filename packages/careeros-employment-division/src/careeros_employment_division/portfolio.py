"""Portfolio summary: projects + top achievements formatted for sharing.

A lightweight seed for Phase 34's full Personal Brand Division — this
just structures what's already in Career Brain, nothing fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from careeros_career_brain import CareerBrain


@dataclass
class PortfolioProject:
    name: str
    description: str
    url: str | None
    skills_used: list[str]


@dataclass
class PortfolioEducation:
    institution: str
    credential: str


@dataclass
class PortfolioCertification:
    name: str
    issuer: str | None


@dataclass
class PortfolioSummary:
    full_name: str
    headline: str
    summary: str = ""
    projects: list[PortfolioProject] = field(default_factory=list)
    highlighted_achievements: list[str] = field(default_factory=list)
    education: list[PortfolioEducation] = field(default_factory=list)
    certifications: list[PortfolioCertification] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)


def build_portfolio_summary(brain: CareerBrain, *, max_achievements: int = 5) -> PortfolioSummary:
    projects = [
        PortfolioProject(
            name=project.name,
            description=project.description,
            url=project.url,
            skills_used=list(project.skills_used),
        )
        for project in brain.projects
    ]

    achievements = []
    for experience in brain.experiences:
        for achievement in experience.achievements:
            text = achievement.description
            if achievement.metric:
                text += f" ({achievement.metric})"
            achievements.append(text)

    education = [
        PortfolioEducation(institution=e.institution, credential=e.credential)
        for e in brain.education
    ]
    certifications = [
        PortfolioCertification(name=c.name, issuer=c.issuer) for c in brain.certifications
    ]
    languages = [f"{lang.name} ({lang.proficiency})" for lang in brain.languages]

    return PortfolioSummary(
        full_name=brain.identity.full_name,
        headline=brain.identity.headline,
        summary=brain.identity.summary,
        projects=projects,
        highlighted_achievements=achievements[:max_achievements],
        education=education,
        certifications=certifications,
        languages=languages,
    )


def render_portfolio_summary(summary: PortfolioSummary) -> str:
    lines = [summary.full_name]
    if summary.headline:
        lines.append(summary.headline)
    lines.append("")

    if summary.summary:
        lines.append(summary.summary)
        lines.append("")

    if summary.projects:
        lines.append("PROJECTS")
        for project in summary.projects:
            line = f"- {project.name}"
            if project.url:
                line += f" ({project.url})"
            lines.append(line)
            if project.description:
                lines.append(f"  {project.description}")
        lines.append("")

    if summary.highlighted_achievements:
        lines.append("HIGHLIGHTED ACHIEVEMENTS")
        lines.extend(f"- {item}" for item in summary.highlighted_achievements)
        lines.append("")

    if summary.education:
        lines.append("EDUCATION")
        for edu in summary.education:
            lines.append(f"- {edu.credential}, {edu.institution}")
        lines.append("")

    if summary.certifications:
        lines.append("CERTIFICATIONS")
        for cert in summary.certifications:
            line = f"- {cert.name}"
            if cert.issuer:
                line += f" — {cert.issuer}"
            lines.append(line)
        lines.append("")

    if summary.languages:
        lines.append("LANGUAGES")
        lines.extend(f"- {item}" for item in summary.languages)

    return "\n".join(lines).strip() + "\n"
