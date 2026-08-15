"""BetaDivision: the facade tying readiness checks and the invite
cohort together — pre-seeded with the platform's own real required
components so a fresh instance already reflects what's actually
shipped.
"""

from __future__ import annotations

from careeros_beta.cohort import (
    BetaCohortRepository,
    BetaInvite,
    accept_invite,
    invite_to_beta,
    is_admitted,
    revoke_invite,
)
from careeros_beta.platform_components import DEFAULT_BETA_COMPONENTS
from careeros_beta.readiness import BetaReadinessReport, verify_beta_readiness
from careeros_common import DocumentStore


class BetaDivision:
    def __init__(self, store: DocumentStore, *, max_seats: int = 100) -> None:
        self._cohort = BetaCohortRepository(store)
        self._max_seats = max_seats

    def check_readiness(self) -> BetaReadinessReport:
        return verify_beta_readiness(DEFAULT_BETA_COMPONENTS)

    def invite(self, email: str) -> BetaInvite:
        return invite_to_beta(self._cohort, email, max_seats=self._max_seats)

    def accept(self, email: str) -> BetaInvite | None:
        return accept_invite(self._cohort, email)

    def revoke(self, email: str) -> BetaInvite | None:
        return revoke_invite(self._cohort, email)

    def is_admitted(self, email: str) -> bool:
        return is_admitted(self._cohort, email)

    def seats_remaining(self) -> int:
        return max(0, self._max_seats - self._cohort.occupied_seats())
