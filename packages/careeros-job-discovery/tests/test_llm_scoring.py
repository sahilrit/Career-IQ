"""Tests for the LLM scoring stage.

The heuristic scorer stays as the cheap first pass; this runs on what
clears it. One structured call does three jobs — correct the scraped
facts, summarise the role neutrally, and score the candidate — so the
tests are mostly about not trusting the model further than we can check.
"""

from __future__ import annotations

import json

import pytest

from careeros_job_discovery.llm_scoring import (
    PATCHABLE_FIELDS,
    LlmJobScorer,
    apply_patches,
    parse_scoring_response,
)
from careeros_job_providers import EmploymentType, JobPosting, Salary


class FakeAIClient:
    """Returns canned completions and records what it was asked."""

    def __init__(self, response: str = "", *, raise_error: Exception | None = None) -> None:
        self._response = response
        self._raise_error = raise_error
        self.calls: list[dict[str, str]] = []

    def complete(self, *, system: str, prompt: str) -> str:
        if self._raise_error is not None:
            raise self._raise_error
        self.calls.append({"system": system, "prompt": prompt})
        return self._response


def _posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "linkedin",
        "external_id": "1",
        "title": "Performance Marketing Manager",
        "company_name": "Acme Corp",
        "url": "https://example.com/jobs/1",
        "location": "London",
        "description": (
            "We need someone to own Google Ads and Meta spend. "
            "The salary is £55,000 to £70,000 per year. "
            "This role is fully remote within the UK."
        ),
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


def _response(**overrides) -> str:
    payload = {
        "score": 82,
        "reason": "Strong paid-acquisition overlap.",
        "brief": {
            "role_summary": "Own paid acquisition end to end.",
            "they_want": ["Google Ads", "Meta"],
            "specifics": ["£55k-£70k"],
            "company_offers": ["Remote"],
            "practical_details": ["Fully remote, UK"],
            "missing_or_unclear": ["Team size"],
            "repeated_signals": ["budget ownership"],
        },
        "patches": [],
        "warnings": [],
    }
    payload.update(overrides)
    return json.dumps(payload)


# --- response parsing --------------------------------------------------------


def test_parses_a_well_formed_response():
    result = parse_scoring_response(_response(), posting=_posting())
    assert result.score == 82
    assert result.reason.startswith("Strong")
    assert result.brief is not None
    assert result.brief.role_summary == "Own paid acquisition end to end."


def test_strips_markdown_code_fences():
    """Most models wrap JSON in ```json fences no matter what you ask."""
    fenced = f"```json\n{_response()}\n```"
    assert parse_scoring_response(fenced, posting=_posting()).score == 82


def test_tolerates_prose_around_the_json():
    noisy = f"Here is the assessment:\n{_response()}\nHope that helps!"
    assert parse_scoring_response(noisy, posting=_posting()).score == 82


def test_a_score_outside_the_range_is_clamped():
    assert parse_scoring_response(_response(score=140), posting=_posting()).score == 100
    assert parse_scoring_response(_response(score=-5), posting=_posting()).score == 0


def test_a_non_numeric_score_is_rejected():
    with pytest.raises(ValueError):
        parse_scoring_response(_response(score="very good"), posting=_posting())


def test_unparseable_output_raises():
    with pytest.raises(ValueError):
        parse_scoring_response("the model said no", posting=_posting())


# --- patch safety ------------------------------------------------------------


def _patch(**overrides) -> dict:
    patch = {
        "field": "salary_min",
        "value": 55000,
        "confidence": "high",
        "evidence": "The salary is £55,000 to £70,000 per year.",
    }
    patch.update(overrides)
    return patch


def test_a_patch_with_verbatim_evidence_survives():
    result = parse_scoring_response(_response(patches=[_patch()]), posting=_posting())
    assert len(result.patches) == 1
    assert result.patches[0].field == "salary_min"


def test_a_patch_whose_evidence_is_not_in_the_posting_is_dropped():
    """The whole point of demanding evidence is checking it. A model that
    invents a supporting quote must not get its correction applied."""
    invented = _patch(evidence="The salary is £200,000 per year.")
    result = parse_scoring_response(_response(patches=[invented]), posting=_posting())
    assert result.patches == []
    assert any("evidence" in w.lower() for w in result.warnings)


def test_evidence_matching_ignores_whitespace_and_case():
    spaced = _patch(evidence="the   SALARY is £55,000\nto £70,000 per year.")
    result = parse_scoring_response(_response(patches=[spaced]), posting=_posting())
    assert len(result.patches) == 1


def test_a_patch_for_a_field_outside_the_whitelist_is_dropped():
    result = parse_scoring_response(
        _response(patches=[_patch(field="url", value="https://evil.example")]),
        posting=_posting(),
    )
    assert result.patches == []


def test_the_whitelist_never_includes_identity_fields():
    """A model must not be able to repoint the apply link or change who the
    posting came from."""
    for field in ("url", "external_id", "source_provider"):
        assert field not in PATCHABLE_FIELDS


def test_a_low_confidence_patch_is_dropped():
    result = parse_scoring_response(
        _response(patches=[_patch(confidence="low")]), posting=_posting()
    )
    assert result.patches == []


def test_a_medium_confidence_patch_may_only_fill_a_missing_value():
    """Medium confidence can add what we don't have; it must not overwrite
    something we already scraped."""
    filled = _posting(salary=Salary(min_amount=40000, max_amount=50000))
    result = parse_scoring_response(
        _response(patches=[_patch(confidence="medium")]), posting=filled
    )
    assert result.patches == []

    empty = _posting(salary=None)
    result = parse_scoring_response(_response(patches=[_patch(confidence="medium")]), posting=empty)
    assert len(result.patches) == 1


# --- applying patches --------------------------------------------------------


def test_apply_patches_corrects_the_salary():
    posting = _posting(salary=None)
    result = parse_scoring_response(
        _response(
            patches=[
                _patch(field="salary_min", value=55000),
                _patch(
                    field="salary_max",
                    value=70000,
                    evidence="The salary is £55,000 to £70,000 per year.",
                ),
            ]
        ),
        posting=posting,
    )
    corrected = apply_patches(posting, result.patches)
    assert corrected.salary is not None
    assert (corrected.salary.min_amount, corrected.salary.max_amount) == (55000, 70000)


def test_apply_patches_can_set_remote():
    posting = _posting(remote=False)
    result = parse_scoring_response(
        _response(
            patches=[
                _patch(
                    field="remote",
                    value=True,
                    evidence="This role is fully remote within the UK.",
                )
            ]
        ),
        posting=posting,
    )
    assert apply_patches(posting, result.patches).remote is True


def test_apply_patches_leaves_the_posting_alone_when_there_are_none():
    posting = _posting()
    assert apply_patches(posting, []) == posting


def test_apply_patches_never_mutates_the_original():
    posting = _posting(salary=None)
    result = parse_scoring_response(_response(patches=[_patch()]), posting=posting)
    apply_patches(posting, result.patches)
    assert posting.salary is None


# --- the scorer --------------------------------------------------------------


def test_scorer_returns_a_result_and_sends_the_posting_text():
    client = FakeAIClient(_response())
    scorer = LlmJobScorer(client)
    result = scorer.score(_posting(), profile_summary="10 years in paid acquisition.")
    assert result is not None
    assert result.score == 82
    assert "Google Ads" in client.calls[0]["prompt"]
    assert "paid acquisition" in client.calls[0]["prompt"]


def test_scorer_returns_none_when_the_ai_call_fails():
    """A scoring failure degrades the result; it must never break discovery."""
    scorer = LlmJobScorer(FakeAIClient(raise_error=RuntimeError("503 overloaded")))
    assert scorer.score(_posting(), profile_summary="x") is None


def test_scorer_returns_none_on_unparseable_output():
    scorer = LlmJobScorer(FakeAIClient("I'm afraid I can't do that"))
    assert scorer.score(_posting(), profile_summary="x") is None


def test_scorer_asks_for_json_only():
    client = FakeAIClient(_response())
    LlmJobScorer(client).score(_posting(), profile_summary="x")
    assert "json" in client.calls[0]["system"].lower()


def test_scorer_truncates_a_very_long_description():
    """Job adverts run to tens of thousands of characters; the prompt has to
    stay bounded or a single posting can blow the context window."""
    client = FakeAIClient(_response())
    LlmJobScorer(client, max_description_chars=200).score(
        _posting(description="x" * 50_000), profile_summary="y"
    )
    assert len(client.calls[0]["prompt"]) < 5_000


def test_apply_patches_can_correct_the_employment_type():
    posting = _posting(employment_type=None, description="This is a 6 month contract role.")
    result = parse_scoring_response(
        _response(
            patches=[
                _patch(
                    field="employment_type",
                    value="contract",
                    evidence="This is a 6 month contract role.",
                )
            ]
        ),
        posting=posting,
    )
    assert len(result.patches) == 1
    assert apply_patches(posting, result.patches).employment_type is EmploymentType.CONTRACT


def test_an_unmappable_employment_type_is_skipped_not_crashed():
    posting = _posting(employment_type=None, description="This is a moonlighting gig role.")
    result = parse_scoring_response(
        _response(
            patches=[
                _patch(
                    field="employment_type",
                    value="moonlighting",
                    evidence="This is a moonlighting gig role.",
                )
            ]
        ),
        posting=posting,
    )
    assert apply_patches(posting, result.patches).employment_type is None


# --- currency safety ---------------------------------------------------------
# Creating a salary from a patch used to default the currency to USD, so a
# GBP posting silently came out as dollars. A wrong currency is worse than a
# missing salary: it makes the number look precise while being wrong by an
# exchange rate.


def test_currency_is_inferred_from_the_evidence():
    posting = _posting(salary=None, description="The salary is £55,000 to £70,000 per year.")
    result = parse_scoring_response(_response(patches=[_patch()]), posting=posting)
    corrected = apply_patches(posting, result.patches)
    assert corrected.salary is not None
    assert corrected.salary.currency == "GBP"


def test_an_explicit_currency_patch_wins_over_inference():
    posting = _posting(salary=None, description="The salary is £55,000 to £70,000 per year.")
    result = parse_scoring_response(
        _response(
            patches=[
                _patch(),
                _patch(
                    field="salary_currency",
                    value="EUR",
                    evidence="The salary is £55,000 to £70,000 per year.",
                ),
            ]
        ),
        posting=posting,
    )
    assert apply_patches(posting, result.patches).salary.currency == "EUR"


def test_an_existing_salary_keeps_its_currency():
    posting = _posting(salary=Salary(min_amount=1, max_amount=2, currency="INR"))
    result = parse_scoring_response(
        _response(patches=[_patch(field="salary_max", value=70000)]), posting=posting
    )
    assert apply_patches(posting, result.patches).salary.currency == "INR"


def test_an_amount_with_no_currency_anywhere_is_dropped():
    """Rather than guess, drop the amount and say why."""
    posting = _posting(salary=None, description="The salary is 55000 to 70000 per year.")
    result = parse_scoring_response(
        _response(patches=[_patch(evidence="The salary is 55000 to 70000 per year.")]),
        posting=posting,
    )
    corrected = apply_patches(posting, result.patches)
    assert corrected.salary is None
