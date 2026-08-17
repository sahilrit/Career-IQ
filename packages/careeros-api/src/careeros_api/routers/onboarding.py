"""Onboarding: a first-run checklist derived from the workspace's real
state, so a new user always knows the next useful step."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_career_brain import CareerBrainRepository

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("")
def checklist(context: Context) -> dict[str, Any]:
    brains = CareerBrainRepository(context.store).list_all()
    brain = brains[0] if brains else None
    has_brain = brain is not None
    has_profile = bool(brain and (brain.skills or brain.experiences))
    has_ai = ai_support.has_workspace_key(context.store, context.account.workspace_id)
    has_applications = bool(brain and brain.applications)

    steps = [
        {
            "key": "brain",
            "label": "Create your Career Brain",
            "href": "/career-brain",
            "done": has_brain,
        },
        {
            "key": "profile",
            "label": "Add your skills & experience (or upload a résumé)",
            "href": "/career-brain",
            "done": has_profile,
        },
        {"key": "ai", "label": "Turn on AI in Settings", "href": "/settings", "done": has_ai},
        {
            "key": "search",
            "label": "Run your first job search",
            "href": "/opportunities",
            "done": has_applications,
        },
    ]
    return {"steps": steps, "complete": all(step["done"] for step in steps)}
