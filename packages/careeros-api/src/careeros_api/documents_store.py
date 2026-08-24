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


def render_document_pdf(document: GeneratedDocument) -> bytes:
    """A typeset PDF of one generated document.

    The résumé/cover-letter content is Markdown (see the application engine's
    renderers), so the export lays it out as a structured CV rather than a
    flat text dump. See ``resume_pdf`` for the layout and the non-latin text
    handling.
    """
    from careeros_api.resume_pdf import render_markdown_pdf

    return render_markdown_pdf(document.title, document.content)
