"""CatalogListing: what the marketplace shows for one plugin, whether
or not it's actually implemented yet. ``is_installable`` is the honest
line between "this really works today" and "this is on the roadmap" —
a listing with no working implementation can be browsed and searched
but not installed.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_plugin_sdk import PluginManifest


class PluginCategory(StrEnum):
    JOB_BOARD = "job_board"
    FREELANCE_PLATFORM = "freelance_platform"
    EMAIL = "email"
    CALENDAR = "calendar"
    DEVELOPER_TOOLS = "developer_tools"
    MARKET_INTELLIGENCE = "market_intelligence"
    ADVERTISING = "advertising"
    ECOMMERCE = "ecommerce"
    OTHER = "other"


class CatalogListing(BaseModel):
    manifest: PluginManifest
    category: PluginCategory
    is_installable: bool = Field(
        description="True only when a real, working Plugin implementation exists."
    )
