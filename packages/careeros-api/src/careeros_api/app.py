"""FastAPI application for CareerOS — the backend the React/Next frontend
consumes (Phase R0). Run with:

    uvicorn careeros_api:app --reload

CORS origins are read from CAREEROS_CORS_ORIGINS (comma-separated); the
frontend's origin goes there in production.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from careeros_api.routers import auth, brain, opportunities, webhooks


def _cors_origins() -> list[str]:
    raw = os.environ.get("CAREEROS_CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(
        title="CareerOS API",
        version="0.1.0",
        summary="HTTP API over the CareerOS domain packages.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(brain.router)
    app.include_router(opportunities.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
