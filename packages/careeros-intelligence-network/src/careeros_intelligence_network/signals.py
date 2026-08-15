"""Anonymous signal contribution: the model has no user_id, workspace_id,
or any other identity-linked field at all — not "identity stripped
before storage" but identity absent from the schema, so a private
Career Brain structurally cannot leak into the network through this
type. ``contribute_signal`` is the only way to create one, and it
requires active ``NETWORK_INTELLIGENCE_SHARING`` consent (Phase 45)
before the anonymous record is ever written.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore
from careeros_intelligence_network.exceptions import ConsentRequiredError
from careeros_trust_layer import ConsentRepository, ConsentType, has_active_consent

_ENTITY_TYPE = "network_signal_contribution"


class SignalCategory(StrEnum):
    RESUME_STRUCTURE = "resume_structure"
    OUTREACH_PATTERN = "outreach_pattern"
    SKILL_DEMAND = "skill_demand"
    INDUSTRY_HIRING = "industry_hiring"
    FREELANCE_NICHE = "freelance_niche"


class SignalContribution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: SignalCategory
    label: str
    weight: float = 1.0
    contributed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SignalContributionRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, contribution: SignalContribution) -> None:
        self._store.put(_ENTITY_TYPE, contribution.id, contribution.model_dump(mode="json"))

    def list_for_category(self, category: SignalCategory) -> list[SignalContribution]:
        return [
            SignalContribution.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("category") == category
        ]

    def list_all(self) -> list[SignalContribution]:
        return [SignalContribution.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]


def contribute_signal(
    repository: SignalContributionRepository,
    consent_repository: ConsentRepository,
    *,
    user_id: str,
    category: SignalCategory,
    label: str,
    weight: float = 1.0,
) -> SignalContribution:
    """``user_id`` is used only to check consent — it is never stored on
    the resulting contribution, so the record itself carries nothing
    that could be traced back to the contributor.
    """
    has_consent = has_active_consent(
        consent_repository, user_id, ConsentType.NETWORK_INTELLIGENCE_SHARING
    )
    if not has_consent:
        raise ConsentRequiredError(
            f"User {user_id!r} has not granted network-intelligence-sharing consent"
        )
    contribution = SignalContribution(category=category, label=label, weight=weight)
    repository.save(contribution)
    return contribution
