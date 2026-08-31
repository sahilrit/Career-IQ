"""Discovery health and application health are different questions.

"Nine ATSes supported" is the kind of claim that is technically true and
practically misleading. An ATS whose jobs CareerOS can read but whose forms it
cannot fill is not the same product feature as one where an application
reaches submission-ready, and reporting a single number for both overstates
what the tool does.

So there are two axes, always reported separately:

    DISCOVERY   — can we read this ATS's postings?
    APPLICATION — can we fill this ATS's forms?

``ApplicationSupport`` is deliberately not a boolean. Greenhouse is the case
that proves it: the integration works, and most of its customers route
applications to their own careers site, so "does application automation work
on Greenhouse" has no yes/no answer. It has a PARTIAL answer with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ApplicationSupport(StrEnum):
    #: Forms open, fill and read back. Verified against live postings.
    AUTOMATED = "automated"
    #: Works for some postings and not others, for a reason we understand and
    #: can state — an employer redirect, a login wall on some tenants.
    PARTIAL = "partial"
    #: Discovery works; there is no form automation at all here.
    DISCOVERY_ONLY = "discovery_only"
    #: Implemented but never verified against a live posting. Never counted as
    #: working — an untested integration is a claim, not a capability.
    UNVERIFIED = "unverified"

    @property
    def is_usable(self) -> bool:
        return self in (ApplicationSupport.AUTOMATED, ApplicationSupport.PARTIAL)


@dataclass(frozen=True)
class AtsCapability:
    ats_id: str
    #: Whether postings can be read at all.
    discovery: bool
    application: ApplicationSupport
    #: Why it is PARTIAL/DISCOVERY_ONLY/UNVERIFIED. Required for anything that
    #: is not AUTOMATED — a limitation with no reason cannot be planned around.
    note: str = ""

    def __post_init__(self) -> None:
        if self.application is not ApplicationSupport.AUTOMATED and not self.note:
            raise ValueError(f"{self.ats_id}: {self.application.value} needs a reason")


#: What each ATS can actually do, as verified by the live smoke tests. Kept
#: here rather than inferred, because "we wrote an adapter" and "we watched a
#: real form fill" are different facts and only the second one counts.
CAPABILITIES: dict[str, AtsCapability] = {
    "greenhouse": AtsCapability(
        "greenhouse",
        discovery=True,
        application=ApplicationSupport.PARTIAL,
        note=(
            "forms hosted on boards.greenhouse.io fill and verify; many customers "
            "route applications to their own careers site instead, which is an "
            "employer choice rather than an integration gap"
        ),
    ),
    "lever": AtsCapability("lever", discovery=True, application=ApplicationSupport.AUTOMATED),
    "ashby": AtsCapability("ashby", discovery=True, application=ApplicationSupport.AUTOMATED),
    "workable": AtsCapability("workable", discovery=True, application=ApplicationSupport.AUTOMATED),
    "smartrecruiters": AtsCapability(
        "smartrecruiters",
        discovery=True,
        application=ApplicationSupport.PARTIAL,
        note=(
            "the application form renders in an iframe; frame-scoped filling is "
            "implemented and verified against fixtures, and live coverage depends "
            "on the tenant's apply flow"
        ),
    ),
    "workday": AtsCapability(
        "workday",
        discovery=True,
        application=ApplicationSupport.DISCOVERY_ONLY,
        note=(
            "Workday requires an account before the application form is reachable; "
            "CareerOS never creates accounts, so these are handed to a human"
        ),
    ),
    "recruitee": AtsCapability(
        "recruitee",
        discovery=True,
        application=ApplicationSupport.UNVERIFIED,
        note="no live application attempt has been run against a Recruitee form yet",
    ),
    "personio": AtsCapability(
        "personio",
        discovery=True,
        application=ApplicationSupport.UNVERIFIED,
        note="no live application attempt has been run against a Personio form yet",
    ),
    "bamboohr": AtsCapability(
        "bamboohr",
        discovery=True,
        application=ApplicationSupport.UNVERIFIED,
        note="no live application attempt has been run against a BambooHR form yet",
    ),
}


def capability_for(ats_id: str) -> AtsCapability:
    """What this ATS can do. Unknown ids are UNVERIFIED, never assumed working."""
    known = CAPABILITIES.get(ats_id)
    if known is not None:
        return known
    return AtsCapability(
        ats_id,
        discovery=True,
        application=ApplicationSupport.UNVERIFIED,
        note="not in the verified capability table",
    )


def application_ready_count() -> int:
    """How many ATSes application automation actually works on.

    The number to quote instead of "nine ATSes supported".
    """
    return sum(1 for c in CAPABILITIES.values() if c.application.is_usable)


def capability_table(health: dict[str, str] | None = None) -> str:
    """The two-column dashboard.

    ``health`` maps ats_id to a live discovery-health string (from each
    provider's ``health_check``); without it the discovery column reports the
    static capability only, and says so.
    """
    rows = [("PROVIDER", "DISCOVERY", "APPLICATION")]
    for ats_id in sorted(CAPABILITIES):
        capability = CAPABILITIES[ats_id]
        if health is not None:
            discovery = health.get(ats_id, "UNKNOWN").upper()
        else:
            discovery = "SUPPORTED" if capability.discovery else "NONE"
        rows.append((ats_id, discovery, capability.application.value.upper()))

    widths = [max(len(row[i]) for row in rows) for i in range(3)]
    lines = [f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]:<{widths[2]}}" for row in rows]
    notes = [f"  {c.ats_id}: {c.note}" for c in CAPABILITIES.values() if c.note]
    if notes:
        lines += ["", "Notes:", *notes]
    return "\n".join(lines)
