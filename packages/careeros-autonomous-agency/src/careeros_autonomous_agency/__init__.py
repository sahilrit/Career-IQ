"""careeros_autonomous_agency: the Autonomous Career Agency — the
platform's final capstone.

Tracks one continuous loop per user:

    Employment / Freelance / Personal Brand -> Networking
      -> Client Success -> Financial Intelligence -> Career Intelligence
      -> CEO Agent -> Learning -> (loop back)

Every stage in that loop is real work an earlier phase's own package
already does — Employment Division (30), Freelance Client Acquisition
(31), Personal Brand (34), CRM (33), Client Success (36), Financial
Intelligence (37), Career Intelligence (40), CEO Agent (41), and
Learning Lab (39). This package adds no new domain logic: it is the
continuous-loop view across all of it, updated automatically from real
events where they exist and by explicit caller confirmation where they
don't — the same honesty Phase 53's onboarding tracker established.
"""

from careeros_autonomous_agency.agency_division import AutonomousAgencyDivision
from careeros_autonomous_agency.cycle_stage import (
    AgencyCycleProgress,
    AgencyCycleProgressRepository,
    AgencyStage,
)
from careeros_autonomous_agency.events import handle_event, wire_agency_cycle
from careeros_autonomous_agency.exceptions import AutonomousAgencyError, CycleNotCompleteError

__all__ = [
    "AgencyCycleProgress",
    "AgencyCycleProgressRepository",
    "AgencyStage",
    "AutonomousAgencyDivision",
    "AutonomousAgencyError",
    "CycleNotCompleteError",
    "handle_event",
    "wire_agency_cycle",
]
