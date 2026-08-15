"""CompanyResearch: structured research notes for an upcoming interview.

CareerOS does not fabricate company facts it can't verify — there is no
default data source here. ``ManualCompanyResearchProvider`` holds
whatever the user (or, later, a real research plugin/AI Skill per Phase
49) has actually entered; an empty/missing field just means "not
researched yet," never an invented answer.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "company_research"


class CompanyResearch(BaseModel):
    calendar_event_id: str
    company_name: str = ""
    business_model: str = ""
    products: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    recent_developments: list[str] = Field(default_factory=list)
    marketing_notes: str = ""
    website_notes: str = ""
    interviewer_backgrounds: dict[str, str] = Field(default_factory=dict)


class CompanyResearchProvider(Protocol):
    def get(self, calendar_event_id: str) -> CompanyResearch | None: ...
    def save(self, research: CompanyResearch) -> None: ...


class ManualCompanyResearchProvider:
    """Research entered by a human (or a future research plugin) — never invented."""

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def get(self, calendar_event_id: str) -> CompanyResearch | None:
        data = self._store.get_or_none(_ENTITY_TYPE, calendar_event_id)
        return CompanyResearch.model_validate(data) if data else None

    def save(self, research: CompanyResearch) -> None:
        self._store.put(_ENTITY_TYPE, research.calendar_event_id, research.model_dump(mode="json"))
