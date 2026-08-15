"""careeros_crm: CRM & Relationship Intelligence.

Tracks every contact (recruiters, founders, CMOs, hiring managers,
agency owners, clients, prospects) through the relationship timeline:

    Viewed -> Liked -> Commented -> Connected -> Messaged -> Conversation
      -> Opportunity -> Client / Employer
"""

from careeros_crm.contact import Contact, ContactRepository, ContactRole
from careeros_crm.crm import RelationshipCRM
from careeros_crm.events import handle_event, wire_crm
from careeros_crm.exceptions import CrmError
from careeros_crm.timeline import (
    Interaction,
    RelationshipStage,
    RelationshipTimeline,
    TimelineRepository,
)

__all__ = [
    "Contact",
    "ContactRepository",
    "ContactRole",
    "CrmError",
    "Interaction",
    "RelationshipCRM",
    "RelationshipStage",
    "RelationshipTimeline",
    "TimelineRepository",
    "handle_event",
    "wire_crm",
]
