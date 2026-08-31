"""The AI reviewer sits ON TOP of the deterministic one, never in place of it.

The deterministic layer checks named entities against the Career Brain, which
is the only authority on what is true, and it cannot hallucinate. The AI layer
catches what pattern matching cannot — a wrong date, an inflated "led", a
paragraph that would fit any candidate — and it can be wrong, so it may only
ever ADD findings.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from careeros_application_engine import AiReviewReport, Severity, review_application_draft
from careeros_career_brain import Achievement, CareerBrain, Experience, Identity, Skill
from careeros_llm import LLMGateway, LLMTask, ProviderHealth, ProviderStatus
from careeros_llm.config import LLMConfig


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        experiences=[
            Experience(
                company_name="Acme",
                title="Growth Lead",
                start_date="2020-01-01",
                is_current=True,
                achievements=[Achievement(description="Ran paid acquisition")],
            )
        ],
        skills=[Skill(name="Google Ads")],
    )


class ScriptedProvider:
    def __init__(self, provider_id: str, answers: list[str]):
        self.provider_id = provider_id
        self.model = f"{provider_id}-model"
        self._answers = list(answers)
        self.calls: list[tuple[str, str]] = []

    def complete(self, *, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        if not self._answers:
            raise RuntimeError("no scripted answer left")
        return self._answers.pop(0)

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.AVAILABLE)


def gateway_of(*providers) -> LLMGateway:
    return LLMGateway(
        providers=list(providers),
        config=LLMConfig(priority=[p.provider_id for p in providers]),
    )


CLEAN_DRAFT = "I ran paid acquisition at Acme as Growth Lead."


class TestTheDeterministicLayerIsAuthoritative:
    def test_it_runs_with_no_ai_at_all(self, brain):
        review = review_application_draft("I led growth at Globex.", brain)
        assert not review.ai_reviewed
        assert review.fabrications
        assert not review.is_safe_to_send

    def test_no_review_at_all_is_not_the_same_as_a_clean_review(self, brain):
        # "no issues found" must say which layers ran, or it reads as an
        # all-clear that nobody actually gave.
        review = review_application_draft(CLEAN_DRAFT, brain)
        assert "deterministic checks only" in review.summary()

    def test_the_ai_layer_cannot_clear_a_deterministic_fabrication(self, brain):
        # A reviewer that finds nothing must not launder a fabricated employer
        # into a safe-to-send draft.
        provider = ScriptedProvider("a", ['{"findings": []}'])
        review = review_application_draft(
            "I led growth at Globex.", brain, gateway=gateway_of(provider)
        )
        assert review.ai_reviewed
        assert review.fabrications
        assert not review.is_safe_to_send


class TestStructuredAiReview:
    def test_findings_are_parsed_and_added(self, brain):
        provider = ScriptedProvider(
            "a",
            [
                '{"findings": [{"severity": "error", "category": "wrong dates",'
                ' "detail": "the draft says 2018, the profile says 2020",'
                ' "evidence": "since 2018"}]}'
            ],
        )
        review = review_application_draft(
            "I have been at Acme since 2018.", brain, gateway=gateway_of(provider)
        )
        assert review.ai_reviewed
        assert review.reviewer_model == "a-model"
        categories = [f.category for f in review.findings]
        assert "wrong dates" in categories

    def test_a_malformed_answer_is_repaired_rather_than_silently_dropped(self, brain):
        # Free-text parsing turned an unparseable answer into "no findings",
        # which reads exactly like a clean review.
        provider = ScriptedProvider(
            "a",
            [
                "The draft looks mostly fine to me!",
                '{"findings": [{"severity": "warning", "category": "generic language",'
                ' "detail": "would fit any candidate", "evidence": "passionate about growth"}]}',
            ],
        )
        review = review_application_draft(CLEAN_DRAFT, brain, gateway=gateway_of(provider))
        assert review.ai_reviewed
        assert [f.category for f in review.findings] == ["generic language"]
        assert len(provider.calls) == 2

    def test_an_unavailable_provider_leaves_ai_reviewed_false(self, brain):
        # Not "reviewed and clean" — not reviewed at all, and the caller must
        # be able to tell.
        empty = LLMGateway(providers=[], config=LLMConfig())
        review = review_application_draft(CLEAN_DRAFT, brain, gateway=empty)
        assert not review.ai_reviewed

    def test_a_finding_with_no_evidence_is_rejected_by_the_schema(self, brain):
        # A finding that cannot quote the text it is about is unactionable,
        # and it is also how a reviewer bluffs.
        assert "evidence" in AiReviewReport.model_json_schema()["$defs"]["AiFinding"]["required"]

    def test_the_prompt_names_every_category_we_require(self, brain):
        provider = ScriptedProvider("a", ['{"findings": []}'])
        review_application_draft(CLEAN_DRAFT, brain, gateway=gateway_of(provider))
        system = provider.calls[0][0].lower()
        for required in (
            "fabricated",
            "unsupported metrics",
            "wrong dates",
            "wrong employer",
            "wrong title",
            "incorrect skills",
            "contradictions",
            "missing requirements",
            "irrelevant",
            "generic language",
        ):
            assert required in system, required


class TestApplicationAnswersAreReviewedToo:
    def test_the_answers_reach_the_reviewer(self, brain):
        provider = ScriptedProvider("a", ['{"findings": []}'])
        review_application_draft(
            CLEAN_DRAFT,
            brain,
            gateway=gateway_of(provider),
            questions={"Are you authorized to work in the US?": "Yes"},
        )
        prompt = provider.calls[0][1]
        assert "authorized to work" in prompt
        assert "Yes" in prompt

    def test_a_wrong_answer_can_be_reported_as_a_fabrication(self, brain):
        provider = ScriptedProvider(
            "a",
            [
                '{"findings": [{"severity": "fabrication", "category":'
                ' "incorrect answer", "detail": "the profile does not record'
                ' US work authorization", "evidence": "Yes"}]}'
            ],
        )
        review = review_application_draft(
            CLEAN_DRAFT,
            brain,
            gateway=gateway_of(provider),
            questions={"Are you authorized to work in the US?": "Yes"},
        )
        assert not review.is_safe_to_send
        assert review.fabrications[0].severity is Severity.FABRICATION


class TestReviewerIndependence:
    def test_the_reviewer_prefers_a_different_provider_than_the_drafter(self):
        # A reviewer running on the same model as the drafter shares its blind
        # spots, which is the whole point of the pair.
        drafter = ScriptedProvider("writer", [])
        reviewer = ScriptedProvider("checker", [])
        gateway = gateway_of(drafter, reviewer)
        assert gateway._chain_for(LLMTask.WRITE)[0].provider_id == "writer"
        assert gateway._review_chain(LLMTask.REVIEW)[0].provider_id == "checker"

    def test_with_one_provider_the_review_still_happens(self):
        only = ScriptedProvider("solo", [])
        gateway = gateway_of(only)
        # Same-model review catches plenty (dates, employers) and is strictly
        # better than no review.
        assert gateway._review_chain(LLMTask.REVIEW)[0].provider_id == "solo"


class TestSchemaShape:
    def test_the_report_is_a_plain_pydantic_model(self):
        assert issubclass(AiReviewReport, BaseModel)
        assert AiReviewReport().findings == []


class TestTheReviewerIsGivenTheFactsItIsAskedToCheck:
    """A false fabrication finding is the most expensive kind.

    It trains the user to ignore findings, which disarms the one layer standing
    between a hallucinated employer and a real application. Observed live: the
    reviewer flagged the candidate's own, correct email as a discrepancy —
    because the facts it was given never contained an email to check against.
    """

    def test_contact_details_reach_the_reviewer(self, brain):
        from careeros_application_engine import profile_facts

        brain.identity.phone = "+44 20 7946 0000"
        brain.identity.links = {"linkedin": "https://linkedin.com/in/ada"}
        facts = profile_facts(brain)
        assert "ada@example.com" in facts
        assert "+44 20 7946 0000" in facts
        assert "linkedin.com/in/ada" in facts

    def test_a_correct_email_answer_is_verifiable_against_the_facts(self, brain):
        provider = ScriptedProvider("a", ['{"findings": []}'])
        review_application_draft(
            CLEAN_DRAFT,
            brain,
            gateway=gateway_of(provider),
            questions={"Email": "ada@example.com"},
        )
        prompt = provider.calls[0][1]
        # The answer AND the fact that verifies it are both in front of the model.
        facts_half, _, _draft = prompt.partition("DRAFT TO REVIEW")
        assert "ada@example.com" in facts_half
