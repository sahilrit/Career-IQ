"""Watchlist domain models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ATS(StrEnum):
    """The applicant-tracking systems we can monitor a company board on.

    CareerOS ships providers for all three; JobOps monitors only Greenhouse,
    Workday and BambooHR, so Lever and Ashby are where our watchlist reaches
    boards theirs cannot.
    """

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"


class WatchedCompany(BaseModel):
    ats: ATS
    #: The company's token in that ATS's URL — e.g. "stripe" in
    #: boards.greenhouse.io/stripe. This plus the ATS is the identity.
    board_token: str
    display_name: str = ""

    @property
    def key(self) -> str:
        return f"{self.ats.value}:{self.board_token}"


class _SeenBoard(BaseModel):
    """The posting ids we have already reported for one board."""

    posting_ids: list[str] = Field(default_factory=list)
