"""The marketplace's seed catalog. Only RemoteOK and Fiverr are
``is_installable=True`` — they're the two providers actually shipped
(Phase 7, 19). Everything else the roadmap names (LinkedIn, Indeed,
Naukri, Upwork, Gmail, Google Calendar, GitHub, Crunchbase, Apollo,
Meta Ads, Shopify) is listed to show the marketplace's intended
breadth, honestly marked catalog-only until a real implementation
exists — never a false claim of working functionality.
"""

from __future__ import annotations

from careeros_plugin_marketplace.catalog import CatalogListing, PluginCategory
from careeros_plugin_sdk import PluginManifest

SEED_CATALOG: list[CatalogListing] = [
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-remoteok",
            name="RemoteOK",
            version="1.0.0",
            description="Discovers remote job postings via RemoteOK's free public API.",
            capabilities=["FIND_JOBS"],
            triggers=["job.discovered"],
            actions=["discover_jobs"],
            health_check_action="discover_jobs",
        ),
        category=PluginCategory.JOB_BOARD,
        is_installable=True,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-fiverr",
            name="Fiverr",
            version="1.0.0",
            description="Discovers freelance gigs on Fiverr via browser automation.",
            capabilities=["FIND_GIGS"],
            triggers=["gig.discovered"],
            actions=["discover_gigs"],
            health_check_action="discover_gigs",
        ),
        category=PluginCategory.FREELANCE_PLATFORM,
        is_installable=True,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-linkedin",
            name="LinkedIn",
            version="0.0.0",
            description="Not yet implemented — planned job discovery and outreach integration.",
            capabilities=[],
        ),
        category=PluginCategory.JOB_BOARD,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-indeed",
            name="Indeed",
            version="0.0.0",
            description="Not yet implemented — planned job discovery integration.",
        ),
        category=PluginCategory.JOB_BOARD,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-naukri",
            name="Naukri",
            version="0.0.0",
            description="Not yet implemented — planned job discovery integration.",
        ),
        category=PluginCategory.JOB_BOARD,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-upwork",
            name="Upwork",
            version="0.0.0",
            description="Not yet implemented — planned freelance gig discovery integration.",
        ),
        category=PluginCategory.FREELANCE_PLATFORM,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-gmail",
            name="Gmail",
            version="0.0.0",
            description="Not yet implemented — planned inbound-email OAuth integration.",
        ),
        category=PluginCategory.EMAIL,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-google-calendar",
            name="Google Calendar",
            version="0.0.0",
            description="Not yet implemented — planned interview scheduling integration.",
        ),
        category=PluginCategory.CALENDAR,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-github",
            name="GitHub",
            version="0.0.0",
            description="Not yet implemented — planned portfolio/project presentation integration.",
        ),
        category=PluginCategory.DEVELOPER_TOOLS,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-crunchbase",
            name="Crunchbase",
            version="0.0.0",
            description="Not yet implemented — planned company/funding signal integration.",
        ),
        category=PluginCategory.MARKET_INTELLIGENCE,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-apollo",
            name="Apollo",
            version="0.0.0",
            description="Not yet implemented — planned decision-maker contact-lookup integration.",
        ),
        category=PluginCategory.MARKET_INTELLIGENCE,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-meta-ads",
            name="Meta Ads",
            version="0.0.0",
            description="Not yet implemented — planned live Ad Library integration.",
        ),
        category=PluginCategory.ADVERTISING,
        is_installable=False,
    ),
    CatalogListing(
        manifest=PluginManifest(
            id="careeros-shopify",
            name="Shopify",
            version="0.0.0",
            description="Not yet implemented — planned live storefront audit integration.",
        ),
        category=PluginCategory.ECOMMERCE,
        is_installable=False,
    ),
]
