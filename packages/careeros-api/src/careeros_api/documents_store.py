"""Persistence for generated application documents (résumé + cover letter),
versioned per application, with a PDF renderer. Stored as tenant-scoped
entities so a workspace only ever sees its own documents."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field

_ENTITY = "generated_document"


class _Store(Protocol):
    def put(self, entity_type: str, entity_id: str, data: dict) -> None: ...
    def get_or_none(self, entity_type: str, entity_id: str) -> dict | None: ...
    def list(self, entity_type: str) -> list[dict]: ...


def _new_id() -> str:
    return str(uuid.uuid4())


class GeneratedDocument(BaseModel):
    id: str = Field(default_factory=_new_id)
    application_id: str
    kind: str  # "resume" | "cover_letter"
    title: str
    content: str
    version: int = 1
    ai_used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentRepository:
    def __init__(self, store: _Store) -> None:
        self._store = store

    def _all(self) -> list[GeneratedDocument]:
        return [GeneratedDocument(**raw) for raw in self._store.list(_ENTITY)]

    def for_application(self, application_id: str) -> list[GeneratedDocument]:
        docs = [d for d in self._all() if d.application_id == application_id]
        return sorted(docs, key=lambda d: (d.kind, d.version))

    def get_or_none(self, document_id: str) -> GeneratedDocument | None:
        raw = self._store.get_or_none(_ENTITY, document_id)
        return GeneratedDocument(**raw) if raw else None

    def save(self, document: GeneratedDocument) -> None:
        self._store.put(_ENTITY, document.id, document.model_dump(mode="json"))

    def _next_version(self, application_id: str, kind: str) -> int:
        versions = [
            d.version for d in self._all() if d.application_id == application_id and d.kind == kind
        ]
        return max(versions, default=0) + 1

    def create(
        self, *, application_id: str, kind: str, title: str, content: str, ai_used: bool
    ) -> GeneratedDocument:
        document = GeneratedDocument(
            application_id=application_id,
            kind=kind,
            title=title,
            content=content,
            ai_used=ai_used,
            version=self._next_version(application_id, kind),
        )
        self.save(document)
        return document


def _latin1(text: str) -> str:
    # FPDF's core fonts are latin-1; replace anything outside it so a stray
    # em-dash or accented name never crashes the export.
    return text.encode("latin-1", "replace").decode("latin-1")


def render_document_pdf(document: GeneratedDocument) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=15)
    pdf.multi_cell(0, 9, _latin1(document.title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", size=11)
    for line in document.content.split("\n"):
        pdf.multi_cell(0, 6, _latin1(line) or " ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return bytes(pdf.output())
