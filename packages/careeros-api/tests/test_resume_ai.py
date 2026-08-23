"""LLM résumé parsing → ParsedResume, with safe fallback on bad output."""

from __future__ import annotations

from careeros_api.resume_ai import ai_parse_resume


class _Client:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def complete(self, *, system: str, prompt: str) -> str:
        return self._reply


_JSON = (
    'Sure: {"experiences":[{"title":"PPC Manager","company":"Presha","start":"2024-05",'
    '"end":"2025-05","description":"Grew orders 650%."}],'
    '"education":[{"credential":"BCA","institution":"Axis","end_year":2023}],'
    '"certifications":[{"name":"Digital Marketing","issuer":"HubSpot"}],'
    '"skills":["Meta Ads","CRO"]}'
)


def test_ai_parse_structures_all_sections():
    parsed = ai_parse_resume("résumé text", _Client(_JSON))
    assert [(e.title, e.company) for e in parsed.experiences] == [("PPC Manager", "Presha")]
    assert parsed.experiences[0].start_date.year == 2024
    assert parsed.experiences[0].end_date.year == 2025
    assert parsed.education[0].credential == "BCA"
    assert parsed.certifications[0].issuer == "HubSpot"
    assert "Meta Ads" in parsed.skills


def test_ai_parse_returns_none_on_non_json():
    assert ai_parse_resume("x", _Client("sorry, no data")) is None
