"""Portfolio page rendering: a single project's public-facing page —
distinct from careeros_employment_division.portfolio, which summarizes
every project across a whole profile. This is per-project, meant for a
personal website or project showcase.
"""

from __future__ import annotations

from careeros_career_brain import Project
from careeros_personal_brand.case_study import CaseStudy


def render_portfolio_page(case_study: CaseStudy, project: Project) -> str:
    lines = [f"# {case_study.title}", ""]
    if project.url:
        lines.append(f"[View project]({project.url})")
        lines.append("")
    lines.append("## Problem")
    lines.append(case_study.problem)
    lines.append("")
    lines.append("## Approach")
    lines.append(case_study.approach)
    lines.append("")
    lines.append("## Result")
    lines.append(case_study.result)
    if project.skills_used:
        lines.append("")
        lines.append(f"**Skills:** {', '.join(project.skills_used)}")
    return "\n".join(lines) + "\n"
