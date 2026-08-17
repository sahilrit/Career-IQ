"""Learning Lab: A/B test your outreach — create experiments, add variants,
log outcomes, and see which variant wins."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_learning_lab import (
    Experiment,
    ExperimentRepository,
    ExperimentType,
    LearningLabDivision,
    OutcomeEvent,
    OutcomeEventRepository,
    OutcomeType,
    Variant,
    VariantRepository,
)

router = APIRouter(prefix="/learning", tags=["learning"])


class ExperimentCreateRequest(BaseModel):
    experiment_type: str = Field(min_length=1)
    name: str = Field(min_length=1)


class VariantCreateRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class OutcomeCreateRequest(BaseModel):
    variant_id: str = Field(min_length=1)
    outcome_type: str = Field(min_length=1)


def _division(context: Context) -> LearningLabDivision:
    store = context.store
    return LearningLabDivision(
        ExperimentRepository(store), VariantRepository(store), OutcomeEventRepository(store)
    )


@router.get("")
def list_experiments(context: Context) -> list[dict[str, Any]]:
    store = context.store
    division = _division(context)
    variants_repo = VariantRepository(store)
    result: list[dict[str, Any]] = []
    for experiment in ExperimentRepository(store).list_all():
        variants = variants_repo.list_for_experiment(experiment.id)
        rows = []
        for variant in variants:
            metrics = division.metrics_for_variant(variant.id)
            rows.append(
                {
                    "id": variant.id,
                    "label": variant.label,
                    "sent": metrics.sent_count,
                    "responses": metrics.response_count,
                    "response_rate": metrics.response_rate,
                }
            )
        result.append(
            {
                "id": experiment.id,
                "name": experiment.name,
                "type": experiment.experiment_type.value,
                "status": experiment.status.value,
                "variants": rows,
                "winner": division.winner_for_experiment(experiment.id),
            }
        )
    return result


@router.post("/experiments", status_code=status.HTTP_201_CREATED)
def create_experiment(body: ExperimentCreateRequest, context: Context) -> dict[str, Any]:
    try:
        experiment_type = ExperimentType(body.experiment_type)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown type") from error
    experiment = Experiment(experiment_type=experiment_type, name=body.name)
    _division(context).create_experiment(experiment)
    return {"id": experiment.id, "name": experiment.name}


@router.post("/variants", status_code=status.HTTP_201_CREATED)
def add_variant(body: VariantCreateRequest, context: Context) -> dict[str, Any]:
    variant = Variant(experiment_id=body.experiment_id, label=body.label)
    _division(context).add_variant(variant)
    return {"id": variant.id, "label": variant.label}


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
def record_outcome(body: OutcomeCreateRequest, context: Context) -> dict[str, Any]:
    try:
        outcome_type = OutcomeType(body.outcome_type)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown outcome") from error
    _division(context).record_outcome(
        OutcomeEvent(variant_id=body.variant_id, outcome_type=outcome_type)
    )
    return {"ok": True}
