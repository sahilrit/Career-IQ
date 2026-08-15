"""EmailMessage: the generic shape any email provider normalizes into.

No real Gmail client lives here — that needs the user's own OAuth app
registration (Phase 26 provides the credential vault + token lifecycle
to hold it once they connect one). ``EmailProvider`` is the extension
point a real integration implements later.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel


class EmailMessage(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime


class EmailProvider(Protocol):
    def fetch_new_messages(self) -> list[EmailMessage]: ...
