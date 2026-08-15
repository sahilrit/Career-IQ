"""Turns classified emails into CareerOS events:

    Email -> Classification -> Event -> Workflow

Publishing on the event bus (Phase 4) is the "workflow" trigger — any
other package (Memory, an interview-prep scheduler, ...) reacts by
subscribing, without this module knowing who's listening.
"""

from __future__ import annotations

from careeros_communication_intelligence.classifier import CommunicationCategory, classify
from careeros_communication_intelligence.models import EmailMessage, EmailProvider
from careeros_event_bus import Event, EventBus

_EVENT_TYPE_BY_CATEGORY: dict[CommunicationCategory, str] = {
    CommunicationCategory.INTERVIEW: "communication.interview_detected",
    CommunicationCategory.REJECTION: "communication.rejection_detected",
    CommunicationCategory.OFFER: "communication.offer_detected",
    CommunicationCategory.RECRUITER_MESSAGE: "communication.recruiter_message_detected",
    CommunicationCategory.FOLLOW_UP: "communication.follow_up_detected",
    CommunicationCategory.CLIENT_INQUIRY: "communication.client_inquiry_detected",
    CommunicationCategory.CONTRACT: "communication.contract_detected",
    CommunicationCategory.PAYMENT: "communication.payment_detected",
}


def process_message(message: EmailMessage, event_bus: EventBus) -> CommunicationCategory:
    """Classify one message and publish the corresponding event, if any.

    OTHER-classified messages are not published as career events — they
    simply aren't career-relevant. Returns the classification either way.
    """
    category = classify(message.subject, message.body)
    event_type = _EVENT_TYPE_BY_CATEGORY.get(category)
    if event_type is not None:
        event_bus.publish(
            Event(
                event_type=event_type,
                source="communication-intelligence",
                payload={
                    "subject_id": message.id,
                    "sender": message.sender,
                    "subject": message.subject,
                },
            )
        )
    return category


def process_all(provider: EmailProvider, event_bus: EventBus) -> list[CommunicationCategory]:
    return [process_message(message, event_bus) for message in provider.fetch_new_messages()]
