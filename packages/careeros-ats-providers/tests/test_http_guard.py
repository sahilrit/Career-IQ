"""The SSRF guard: adapters derive URLs from config, so the final URL is checked."""

from __future__ import annotations

import pytest

from careeros_ats_providers import BoardFetchError, assert_allowed

HOSTS = frozenset({"api.example.com", ".tenant.example.org"})


class TestAssertAllowed:
    def test_allows_an_exact_host(self):
        assert assert_allowed("https://api.example.com/v1/jobs", HOSTS, ats="x")

    def test_allows_a_subdomain_of_a_suffix_entry(self):
        # Workday and BambooHR are per-tenant, so subdomains must be allowed.
        assert assert_allowed("https://acme.tenant.example.org/list", HOSTS, ats="x")

    def test_rejects_another_host(self):
        with pytest.raises(BoardFetchError, match="untrusted host"):
            assert_allowed("https://evil.example.net/steal", HOSTS, ats="x")

    def test_rejects_a_lookalike_suffix(self):
        # "notexample.org" must not pass a ".example.org" rule via endswith.
        with pytest.raises(BoardFetchError, match="untrusted host"):
            assert_allowed("https://evil-tenant.example.org.attacker.net/x", HOSTS, ats="x")

    def test_rejects_plain_http(self):
        with pytest.raises(BoardFetchError, match="HTTPS"):
            assert_allowed("http://api.example.com/v1", HOSTS, ats="x")

    def test_rejects_a_non_url(self):
        with pytest.raises(BoardFetchError):
            assert_allowed("file:///etc/passwd", HOSTS, ats="x")

    def test_host_comparison_is_case_insensitive(self):
        assert assert_allowed("https://API.EXAMPLE.COM/v1", HOSTS, ats="x")
