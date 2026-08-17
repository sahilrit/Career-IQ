"""Autopilot endpoint: the workspace's autonomous-apply run history.

Runs themselves are produced by the autopilot daemon / dashboard (they
drive a headless browser); the API surfaces the recorded outcomes so the
React app can show what ran while nobody was watching. Read straight from
the tenant-scoped store to avoid pulling the browser-heavy autopilot
package into the API image.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from careeros_api.dependencies import Context
from careeros_api.schemas import AutopilotOutcome, AutopilotRunResponse

_RUN_ENTITY_TYPE = "autopilot_run"

router = APIRouter(prefix="/autopilot", tags=["autopilot"])


def _to_response(run: dict[str, Any]) -> AutopilotRunResponse:
    return AutopilotRunResponse(
        id=str(run.get("id", "")),
        ran_at=str(run.get("ran_at", "")),
        discovered=int(run.get("discovered", 0)),
        submitted=int(run.get("submitted", 0)),
        qualified_total=int(run.get("qualified_total", 0)),
        outcomes=[
            AutopilotOutcome(
                job_title=str(outcome.get("job_title", "?")),
                company_name=str(outcome.get("company_name", "?")),
                submitted=bool(outcome.get("submitted", False)),
                reason=str(outcome.get("reason", "")),
            )
            for outcome in run.get("outcomes", [])
        ],
    )


@router.get("/runs", response_model=list[AutopilotRunResponse])
def list_runs(context: Context) -> list[AutopilotRunResponse]:
    runs = context.store.list(_RUN_ENTITY_TYPE)
    runs.sort(key=lambda run: run.get("ran_at", ""), reverse=True)
    return [_to_response(run) for run in runs]
