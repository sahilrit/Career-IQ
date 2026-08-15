"""Case study generation: the root asset every other Personal Brand
artifact (portfolio page, LinkedIn post, X thread, blog post, resume
achievement) is built from. Deterministic — the "result" comes from the
user's real, TF-IDF-ranked achievements (Phase 11) when one is
relevant; nothing is invented when none is.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_career_brain import CareerBrain, Project
from careeros_career_brain_engine import rank_achievements_for_text

_FALLBACK_RESULT = "Shipped and in active use."


class CaseStudy(BaseModel):
    project_id: str
    title: str
    problem: str
    approach: str
    result: str


def generate_case_study(brain: CareerBrain, project: Project) -> CaseStudy:
    problem = project.description or f"{project.name} needed to be built."
    approach = (
        f"Built {project.name} using {', '.join(project.skills_used)}."
        if project.skills_used
        else f"Built {project.name}."
    )

    text = f"{project.name} {project.description}"
    ranked = rank_achievements_for_text(brain, text, top_k=1)
    if ranked:
        achievement = ranked[0].achievement
        result = achievement.description
        if achievement.metric:
            result += f" ({achievement.metric})"
    else:
        result = _FALLBACK_RESULT

    return CaseStudy(
        project_id=project.id,
        title=project.name,
        problem=problem,
        approach=approach,
        result=result,
    )
