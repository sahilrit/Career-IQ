"""Career Brain read endpoints — proves the tenant-scoped stack end to
end. Writes and the rest of the surface arrive in later phases."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context
from careeros_career_brain import CareerBrainRepository

router = APIRouter(tags=["brain"])


@router.get("/brain")
def get_brain(context: Context) -> dict[str, Any]:
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no Career Brain in this workspace")
    return brains[0].model_dump(mode="json")


@router.get("/applications")
def list_applications(context: Context) -> list[dict[str, Any]]:
    return [
        application.model_dump(mode="json")
        for brain in CareerBrainRepository(context.store).list_all()
        for application in brain.applications
    ]
