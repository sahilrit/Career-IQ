"""careeros_communication_intelligence: Email -> Classification -> Event
-> Workflow. Zero-cost keyword classification now; a pluggable
EmailProvider interface for a real Gmail/OAuth integration later.
"""

from careeros_communication_intelligence.classifier import CommunicationCategory, classify
from careeros_communication_intelligence.events import process_all, process_message
from careeros_communication_intelligence.models import EmailMessage, EmailProvider

__all__ = [
    "CommunicationCategory",
    "EmailMessage",
    "EmailProvider",
    "classify",
    "process_all",
    "process_message",
]
