"""Testimonials: social proof, always user-supplied — never generated
or inferred. Someone said this about the user's work; CareerOS just
stores and surfaces it.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "testimonial"


class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author_name: str
    author_title: str = ""
    quote: str
    project_id: str | None = None


class TestimonialRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, testimonial: Testimonial) -> None:
        self._store.put(_ENTITY_TYPE, testimonial.id, testimonial.model_dump(mode="json"))

    def list_all(self) -> list[Testimonial]:
        return [Testimonial.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_for_project(self, project_id: str) -> list[Testimonial]:
        return [t for t in self.list_all() if t.project_id == project_id]
