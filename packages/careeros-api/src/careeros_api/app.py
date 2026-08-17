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

from careeros_api.routers import (
    admin,
    auth,
    autopilot,
    billing,
    brain,
    career_intel,
    ceo,
    client_success,
    finance,
    freelance,
    interview,
    learning,
    network,
    offers,
    opportunities,
    personal_brand,
    settings,
    webhooks,
)


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
    app.include_router(offers.router)
    app.include_router(network.router)
    app.include_router(freelance.router)
    app.include_router(billing.router)
    app.include_router(autopilot.router)
    app.include_router(admin.router)
    app.include_router(settings.router)
    app.include_router(interview.router)
    app.include_router(personal_brand.router)
    app.include_router(client_success.router)
    app.include_router(ceo.router)
    app.include_router(learning.router)
    app.include_router(finance.router)
    app.include_router(career_intel.router)
    app.include_router(webhooks.router)
    return app


app = create_app()
