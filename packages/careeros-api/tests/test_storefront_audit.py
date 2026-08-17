"""The browser-free storefront auditor: real HTML in, findings out."""

from __future__ import annotations

import httpx

from careeros_api.storefront_audit import audit_storefront


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_bare_page_flags_every_missing_signal():
    client = _client(lambda r: httpx.Response(200, text="<html><body>Buy stuff</body></html>"))
    findings = audit_storefront("acme.com", http_client=client)
    assert len(findings) == 6  # nothing present → every check fires


def test_well_optimized_page_has_no_findings():
    html = (
        '<html><head><meta name="viewport" content="width=device-width"></head>'
        "<body>Free shipping · 5-star reviews on Trustpilot · money-back guarantee · "
        "limited stock · Shop Pay express checkout</body></html>"
    )
    client = _client(lambda r: httpx.Response(200, text=html))
    assert audit_storefront("acme.com", http_client=client) == []


def test_unreachable_site_degrades_to_empty():
    def boom(request):
        raise httpx.ConnectError("nope")

    assert audit_storefront("acme.com", http_client=_client(boom)) == []
    client = _client(lambda r: httpx.Response(404, text="not found"))
    assert audit_storefront("acme.com", http_client=client) == []
