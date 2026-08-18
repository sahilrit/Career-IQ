"""Generated application documents: list versions attached to an application,
edit their text, and export a clean PDF."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from careeros_api.dependencies import Context
from careeros_api.documents_store import DocumentRepository, render_document_pdf
from careeros_tenancy import Permission

router = APIRouter(tags=["documents"])


class DocumentEditRequest(BaseModel):
    content: str


@router.get("/applications/{application_id}/documents")
def list_documents(application_id: str, context: Context) -> list[dict[str, Any]]:
    repo = DocumentRepository(context.store)
    return [d.model_dump(mode="json") for d in repo.for_application(application_id)]


@router.patch("/documents/{document_id}")
def edit_document(document_id: str, body: DocumentEditRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    repo = DocumentRepository(context.store)
    document = repo.get_or_none(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    document.content = body.content
    repo.save(document)
    return document.model_dump(mode="json")


@router.get("/documents/{document_id}/pdf")
def download_document_pdf(document_id: str, context: Context) -> Response:
    repo = DocumentRepository(context.store)
    document = repo.get_or_none(document_id)
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    pdf = render_document_pdf(document)
    filename = f"{document.kind}-v{document.version}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
