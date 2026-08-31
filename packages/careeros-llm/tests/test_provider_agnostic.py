"""The application engine must not know or care which model answered.

The requirement is stronger than "it works with more than one vendor": the same
task, run through different providers, must produce the SAME SHAPE. Otherwise
every downstream caller grows a branch per vendor, and the gateway has bought
nothing.

Structured output is what makes this true by construction — the schema is the
contract, and a provider whose answer does not fit it is rejected rather than
passed along in a vendor-specific shape.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from careeros_llm import LLMGateway, LLMTask, ProviderHealth, ProviderStatus
from careeros_llm.config import LLMConfig


class Qualification(BaseModel):
    """The Career Brain task from the spec: is this candidate qualified, and
    which of their achievements are relevant."""

    qualified: bool
    score: int = Field(ge=0, le=100)
    relevant_achievements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)


class VendorProvider:
    """A provider whose answers are shaped the way that vendor tends to reply."""

    def __init__(self, provider_id: str, answers: list[str]):
        self.provider_id = provider_id
        self.model = f"{provider_id}-model"
        self._answers = list(answers)

    def complete(self, *, system: str, prompt: str) -> str:
        return self._answers.pop(0)

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.AVAILABLE)


PAYLOAD = {
    "qualified": True,
    "score": 82,
    "relevant_achievements": ["Ran paid acquisition on Google and Meta"],
    "missing_requirements": ["$1M+ budget ownership"],
}

#: The same answer, packaged the way different vendors actually package it:
#: bare JSON, fenced JSON, and JSON behind a chatty preamble.
VENDOR_STYLES = {
    "vendor-a": '{"qualified": true, "score": 82, '
    '"relevant_achievements": ["Ran paid acquisition on Google and Meta"], '
    '"missing_requirements": ["$1M+ budget ownership"]}',
    "vendor-b": '```json\n{"qualified": true, "score": 82, '
    '"relevant_achievements": ["Ran paid acquisition on Google and Meta"], '
    '"missing_requirements": ["$1M+ budget ownership"]}\n```',
    "vendor-c": 'Here is my assessment:\n{"qualified": true, "score": 82, '
    '"relevant_achievements": ["Ran paid acquisition on Google and Meta"], '
    '"missing_requirements": ["$1M+ budget ownership"]}',
}

SYSTEM = "You assess qualification from verified candidate facts only."
PROMPT = "Determine qualification and identify relevant career achievements."


def gateway_for(provider_id: str) -> LLMGateway:
    provider = VendorProvider(provider_id, [VENDOR_STYLES[provider_id]])
    return LLMGateway(providers=[provider], config=LLMConfig(priority=[provider_id]))


class TestSameTaskEveryProvider:
    @pytest.mark.parametrize("provider_id", sorted(VENDOR_STYLES))
    def test_each_provider_produces_the_same_validated_object(self, provider_id):
        response = gateway_for(provider_id).complete_structured(
            task=LLMTask.ANALYZE, system=SYSTEM, prompt=PROMPT, schema=Qualification
        )
        assert response.value.model_dump() == PAYLOAD
        # And the provenance still says who answered.
        assert response.run.provider_id == provider_id

    def test_the_results_are_indistinguishable_across_providers(self):
        results = [
            gateway_for(provider_id)
            .complete_structured(
                task=LLMTask.ANALYZE, system=SYSTEM, prompt=PROMPT, schema=Qualification
            )
            .value.model_dump()
            for provider_id in sorted(VENDOR_STYLES)
        ]
        assert all(result == results[0] for result in results)

    def test_the_type_is_the_same_regardless_of_vendor(self):
        for provider_id in VENDOR_STYLES:
            value = (
                gateway_for(provider_id)
                .complete_structured(
                    task=LLMTask.ANALYZE, system=SYSTEM, prompt=PROMPT, schema=Qualification
                )
                .value
            )
            assert isinstance(value, Qualification)

    def test_a_vendor_that_answers_in_a_different_shape_is_rejected_not_passed_on(self):
        # The protection that makes the above true: a provider cannot smuggle a
        # vendor-specific shape past the schema and force callers to branch.
        odd = VendorProvider(
            "vendor-d",
            [
                '{"is_qualified": "yes", "rating": "8/10"}',
                '{"is_qualified": "yes", "rating": "8/10"}',
            ],
        )
        good = VendorProvider("vendor-a", [VENDOR_STYLES["vendor-a"]])
        gateway = LLMGateway(
            providers=[odd, good], config=LLMConfig(priority=["vendor-d", "vendor-a"])
        )
        response = gateway.complete_structured(
            task=LLMTask.ANALYZE, system=SYSTEM, prompt=PROMPT, schema=Qualification
        )
        assert response.value.model_dump() == PAYLOAD
        assert response.run.provider_id == "vendor-a"


class TestBusinessLogicNamesNoVendor:
    def test_callers_ask_for_a_task_not_a_model(self):
        # LLMTask is the whole vocabulary business logic has. Nothing in it
        # names a vendor, so swapping providers is a config change.
        assert {t.value for t in LLMTask} == {
            "classify",
            "extract",
            "analyze",
            "write",
            "answer",
            "review",
        }

    def test_no_business_package_imports_a_vendor_sdk(self):
        # The seam only holds if nothing bypasses it.
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[3]
        offenders = []
        for path in root.glob("packages/careeros-*/src/**/*.py"):
            # careeros-ai IS the vendor transport layer; careeros-llm wraps it.
            if "careeros-ai/" in str(path) or "careeros-llm/" in str(path):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "import anthropic" in text or "import openai" in text:
                offenders.append(str(path.relative_to(root)))
        assert offenders == []
