"""Tests for the deterministic email classifier."""

from __future__ import annotations

from careeros_communication_intelligence import CommunicationCategory, classify


def test_offer_email():
    result = classify(
        "Your offer from Acme", "We are pleased to offer you the Backend Engineer position."
    )
    assert result == CommunicationCategory.OFFER


def test_rejection_email():
    result = classify(
        "Update on your application",
        "Unfortunately, we have decided not to move forward with your application.",
    )
    assert result == CommunicationCategory.REJECTION


def test_interview_email():
    result = classify(
        "Let's schedule a call", "We'd like to schedule a call for a technical screen next week."
    )
    assert result == CommunicationCategory.INTERVIEW


def test_ambiguous_rejection_after_interview_is_classified_as_rejection():
    result = classify(
        "Following up on your interview",
        "Unfortunately, after your interview, we've decided to move forward with other candidates.",
    )
    assert result == CommunicationCategory.REJECTION


def test_contract_email():
    result = classify("Contract attached", "Please find the statement of work attached.")
    assert result == CommunicationCategory.CONTRACT


def test_payment_email():
    result = classify("Invoice #1042", "Your invoice payment has been sent via wire transfer.")
    assert result == CommunicationCategory.PAYMENT


def test_recruiter_message():
    result = classify(
        "Opportunity at Acme", "Hi, I'm a recruiter and came across your profile on LinkedIn."
    )
    assert result == CommunicationCategory.RECRUITER_MESSAGE


def test_client_inquiry():
    result = classify(
        "Project inquiry", "I'm looking for a freelancer to help redesign our Shopify store."
    )
    assert result == CommunicationCategory.CLIENT_INQUIRY


def test_follow_up():
    result = classify("Checking in", "Just checking in — any update on the proposal I sent?")
    assert result == CommunicationCategory.FOLLOW_UP


def test_unrelated_email_is_other():
    result = classify("Your Amazon order shipped", "Your package is on its way.")
    assert result == CommunicationCategory.OTHER
