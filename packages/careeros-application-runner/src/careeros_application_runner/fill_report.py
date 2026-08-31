"""What actually happened to every field on a form.

The old fill path wrapped each field in ``contextlib.suppress(Exception)``, so
a form could report success having written almost nothing: a rejected field, a
missing selector and a genuinely-filled field were indistinguishable
afterwards. That is the single biggest reason "application filling is
unreliable" — not that fills failed, but that failures were invisible.

Every field now produces a ``FieldResult`` with a reason, and the report knows
the difference between "this form is ready for a human to submit" and "this
form is missing things a human must supply".
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class FieldOutcome(StrEnum):
    #: Written AND read back with the expected value.
    FILLED = "filled"
    #: Written, but the value could not be read back to confirm it. The field
    #: may well be fine (a rich-text editor, a masked input); it is reported
    #: separately so a human knows exactly what to eyeball.
    UNVERIFIED = "unverified"
    #: The field is on the page but we have no truthful value for it. This is a
    #: success of the zero-fabrication rule, not a failure.
    NEEDS_HUMAN = "needs_human"
    #: The selector is not on this page at all.
    NOT_PRESENT = "not_present"
    #: We had a value and tried to write it, and it did not take.
    FAILED = "failed"


class FieldResult(BaseModel):
    #: Canonical name ("email", "first_name") or the question label.
    field: str
    selector: str
    outcome: FieldOutcome
    #: Why - always populated for anything that is not FILLED.
    detail: str = ""
    #: Whether the field is one the form marks required.
    required: bool = False

    @property
    def ok(self) -> bool:
        return self.outcome in (FieldOutcome.FILLED, FieldOutcome.UNVERIFIED)


class FillReport(BaseModel):
    """The evidence record for one fill attempt."""

    results: list[FieldResult] = Field(default_factory=list)

    def add(self, result: FieldResult) -> None:
        self.results.append(result)

    def _of(self, *outcomes: FieldOutcome) -> list[FieldResult]:
        return [r for r in self.results if r.outcome in outcomes]

    @property
    def filled(self) -> list[FieldResult]:
        return self._of(FieldOutcome.FILLED)

    @property
    def unverified(self) -> list[FieldResult]:
        return self._of(FieldOutcome.UNVERIFIED)

    @property
    def failures(self) -> list[FieldResult]:
        return self._of(FieldOutcome.FAILED)

    @property
    def needs_human(self) -> list[FieldResult]:
        """Fields deliberately left blank because no truthful value existed."""
        return self._of(FieldOutcome.NEEDS_HUMAN)

    @property
    def blocking(self) -> list[FieldResult]:
        """What stands between this form and a submission.

        A required field that failed or was left for a human blocks; an
        optional one does not. A field that was never on the page cannot block,
        because there is nothing to fill.
        """
        return [
            r
            for r in self.results
            if r.required and r.outcome in (FieldOutcome.FAILED, FieldOutcome.NEEDS_HUMAN)
        ]

    @property
    def is_submittable(self) -> bool:
        """No required field is missing and nothing failed outright."""
        return not self.blocking and not self.failures

    def summary(self) -> str:
        """One line a human can act on."""
        parts = [f"{len(self.filled)} filled"]
        if self.unverified:
            parts.append(f"{len(self.unverified)} unverified")
        if self.needs_human:
            parts.append(f"{len(self.needs_human)} need you")
        if self.failures:
            parts.append(f"{len(self.failures)} FAILED")
        return ", ".join(parts)
