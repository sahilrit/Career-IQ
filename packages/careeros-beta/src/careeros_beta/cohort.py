"""Beta cohort: a capacity-limited invite list — "start with a limited
number of users" as a real, enforced gate rather than a promise. Every
grant or revocation is its own record, the same auditable-history
philosophy as Phase 45's consent records.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_beta.exceptions import BetaCohortFullError
from careeros_common import DocumentStore

_ENTITY_TYPE = "beta_invite"


class InviteStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"


class BetaInvite(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    status: InviteStatus = InviteStatus.PENDING
    invited_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BetaCohortRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, invite: BetaInvite) -> None:
        self._store.put(_ENTITY_TYPE, invite.id, invite.model_dump(mode="json"))

    def find_by_email(self, email: str) -> BetaInvite | None:
        for data in self._store.list(_ENTITY_TYPE):
            if data.get("email") == email:
                return BetaInvite.model_validate(data)
        return None

    def list_all(self) -> list[BetaInvite]:
        return [BetaInvite.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def occupied_seats(self) -> int:
        return sum(1 for invite in self.list_all() if invite.status != InviteStatus.REVOKED)


def invite_to_beta(repository: BetaCohortRepository, email: str, *, max_seats: int) -> BetaInvite:
    existing = repository.find_by_email(email)
    if existing is not None and existing.status != InviteStatus.REVOKED:
        return existing
    if repository.occupied_seats() >= max_seats:
        raise BetaCohortFullError(f"Beta cohort is full ({max_seats} seats occupied)")
    invite = BetaInvite(email=email)
    repository.save(invite)
    return invite


def accept_invite(repository: BetaCohortRepository, email: str) -> BetaInvite | None:
    invite = repository.find_by_email(email)
    if invite is None or invite.status == InviteStatus.REVOKED:
        return None
    invite.status = InviteStatus.ACCEPTED
    repository.save(invite)
    return invite


def revoke_invite(repository: BetaCohortRepository, email: str) -> BetaInvite | None:
    invite = repository.find_by_email(email)
    if invite is None:
        return None
    invite.status = InviteStatus.REVOKED
    repository.save(invite)
    return invite


def is_admitted(repository: BetaCohortRepository, email: str) -> bool:
    invite = repository.find_by_email(email)
    return invite is not None and invite.status == InviteStatus.ACCEPTED
