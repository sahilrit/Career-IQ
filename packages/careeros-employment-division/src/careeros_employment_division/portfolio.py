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
class PortfolioSummary:
    full_name: str
    headline: str
    projects: list[PortfolioProject] = field(default_factory=list)
    highlighted_achievements: list[str] = field(default_factory=list)


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

    return PortfolioSummary(
        full_name=brain.identity.full_name,
        headline=brain.identity.headline,
        projects=projects,
        highlighted_achievements=achievements[:max_achievements],
    )


def render_portfolio_summary(summary: PortfolioSummary) -> str:
    lines = [summary.full_name]
    if summary.headline:
        lines.append(summary.headline)
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

    return "\n".join(lines).strip() + "\n"
