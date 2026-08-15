"""Tests for EventContractRegistry."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from careeros_core import ContractViolationError, EventContractRegistry
from careeros_event_bus import Event, EventBus


class ApplicationSubmittedPayload(BaseModel):
    subject_id: str
    company_name: str


def test_event_with_no_registered_contract_publishes_unchanged():
    bus = EventBus()
    contracts = EventContractRegistry()
    event = Event(event_type="job.discovered", payload={"anything": "goes"})

    contracts.publish(bus, event)

    assert bus.history()[0] is event


def test_event_matching_its_contract_publishes_successfully():
    bus = EventBus()
    contracts = EventContractRegistry()
    contracts.register("application.autonomously_submitted", ApplicationSubmittedPayload)
    event = Event(
        event_type="application.autonomously_submitted",
        payload={"subject_id": "app-1", "company_name": "Acme"},
    )

    contracts.publish(bus, event)

    assert len(bus.history()) == 1


def test_event_violating_its_contract_raises_and_is_not_published():
    bus = EventBus()
    contracts = EventContractRegistry()
    contracts.register("application.autonomously_submitted", ApplicationSubmittedPayload)
    event = Event(event_type="application.autonomously_submitted", payload={"missing": "fields"})

    with pytest.raises(ContractViolationError):
        contracts.publish(bus, event)

    assert bus.history() == []


def test_validate_alone_does_not_publish():
    bus = EventBus()
    contracts = EventContractRegistry()
    contracts.register("application.autonomously_submitted", ApplicationSubmittedPayload)
    event = Event(
        event_type="application.autonomously_submitted",
        payload={"subject_id": "app-1", "company_name": "Acme"},
    )

    contracts.validate(event)  # must not raise, must not publish

    assert bus.history() == []
