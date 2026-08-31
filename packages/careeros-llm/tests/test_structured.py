"""Structured output: parse, validate, repair, fall back — never guess.

The failure this prevents is the quiet one. A model that answers "roughly 7 out
of 10" where a float was expected does not blow up at the call site; it blows
up three functions later in code that has no idea an LLM was involved.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from careeros_llm import (
    LLMGateway,
    LLMTask,
    NoProviderAvailableError,
    ProviderCallError,
    ProviderHealth,
    ProviderStatus,
    extract_json,
    parse_structured,
)
from careeros_llm.config import LLMConfig


class Analysis(BaseModel):
    qualified: bool
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)


class ScriptedProvider:
    """Returns a queued answer per call, so a repair round-trip is observable."""

    def __init__(self, provider_id: str, answers: list[str], *, raises: Exception | None = None):
        self.provider_id = provider_id
        self.model = f"{provider_id}-model"
        self._answers = list(answers)
        self._raises = raises
        self.calls: list[tuple[str, str]] = []

    def complete(self, *, system: str, prompt: str) -> str:
        self.calls.append((system, prompt))
        if self._raises is not None:
            raise self._raises
        return self._answers.pop(0) if self._answers else ""

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(provider_id=self.provider_id, status=ProviderStatus.AVAILABLE)


def gateway(providers) -> LLMGateway:
    return LLMGateway(
        providers=providers, config=LLMConfig(priority=[p.provider_id for p in providers])
    )


class TestExtraction:
    def test_plain_json(self):
        assert extract_json('{"a": 1}') == {"a": 1}

    def test_markdown_fenced_json(self):
        assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_after_a_chatty_preamble(self):
        assert extract_json('Sure! Here you go:\n{"a": 1}') == {"a": 1}

    def test_empty_response_is_an_error_not_an_empty_object(self):
        with pytest.raises(ValueError, match="empty"):
            extract_json("   ")

    def test_prose_with_no_json_is_an_error(self):
        with pytest.raises(ValueError, match="did not contain"):
            extract_json("I'd say roughly 7 out of 10.")

    def test_malformed_json_is_never_repaired_into_a_guess(self):
        # A "fixed" object is a guess about what the model meant.
        with pytest.raises(ValueError):
            extract_json('{"a": 1,,,}')


class TestValidation:
    def test_valid_payload_becomes_the_model(self):
        value = parse_structured('{"qualified": true, "score": 80}', Analysis)
        assert value.qualified is True
        assert value.score == 80

    def test_out_of_range_value_is_rejected(self):
        with pytest.raises(ValueError, match="did not match the schema"):
            parse_structured('{"qualified": true, "score": 900}', Analysis)

    def test_missing_required_field_is_rejected(self):
        with pytest.raises(ValueError, match="did not match the schema"):
            parse_structured('{"score": 10}', Analysis)

    def test_a_json_array_is_rejected_for_an_object_schema(self):
        with pytest.raises(ValueError, match="not the required object"):
            parse_structured("[1, 2, 3]", Analysis)

    def test_the_error_names_the_offending_field(self):
        with pytest.raises(ValueError, match="score"):
            parse_structured('{"qualified": true, "score": 900}', Analysis)


class TestGatewayStructured:
    def test_valid_first_answer_needs_no_retry(self):
        provider = ScriptedProvider("a", ['{"qualified": true, "score": 70}'])
        response = gateway([provider]).complete_structured(
            task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
        )
        assert response.value.score == 70
        assert response.run.retries == 0
        assert len(provider.calls) == 1

    def test_the_schema_is_put_in_front_of_the_model(self):
        provider = ScriptedProvider("a", ['{"qualified": false, "score": 0}'])
        gateway([provider]).complete_structured(
            task=LLMTask.ANALYZE, system="BE TRUTHFUL", prompt="p", schema=Analysis
        )
        system = provider.calls[0][0]
        assert "BE TRUTHFUL" in system
        assert "qualified" in system and "score" in system

    def test_malformed_output_is_repaired_against_the_same_provider(self):
        provider = ScriptedProvider(
            "a", ["I think they're a good fit!", '{"qualified": true, "score": 55}']
        )
        response = gateway([provider]).complete_structured(
            task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
        )
        assert response.value.score == 55
        assert response.run.retries == 1
        # The repair must quote back what was wrong, or it is just a re-roll.
        assert "REJECTED" in provider.calls[1][1]

    def test_repairs_are_bounded_then_the_next_provider_is_tried(self):
        stubborn = ScriptedProvider("a", ["nope", "still nope", "never json"])
        good = ScriptedProvider("b", ['{"qualified": true, "score": 42}'])
        response = gateway([stubborn, good]).complete_structured(
            task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
        )
        assert response.value.score == 42
        assert response.run.provider_id == "b"
        # One repair, then abandoned — not an unbounded loop.
        assert len(stubborn.calls) == 2

    def test_a_non_retryable_failure_is_not_repaired_against_the_same_provider(self):
        # "Not logged in" cannot be fixed by asking again; asking again just
        # costs the user another CLI timeout.
        broken = ScriptedProvider(
            "a", [], raises=ProviderCallError("a", "Not logged in · Please run /login")
        )
        good = ScriptedProvider("b", ['{"qualified": true, "score": 1}'])
        response = gateway([broken, good]).complete_structured(
            task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
        )
        assert response.run.provider_id == "b"
        assert len(broken.calls) == 1

    def test_every_provider_failing_raises_with_all_the_reasons(self):
        a = ScriptedProvider("a", [], raises=ProviderCallError("a", "Not logged in"))
        b = ScriptedProvider("b", ["prose", "more prose"])
        with pytest.raises(NoProviderAvailableError) as caught:
            gateway([a, b]).complete_structured(
                task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
            )
        message = str(caught.value)
        assert "Not logged in" in message
        assert "b:" in message

    def test_no_provider_at_all_raises_rather_than_returning_a_blank_object(self):
        with pytest.raises(NoProviderAvailableError):
            LLMGateway(providers=[], config=LLMConfig()).complete_structured(
                task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
            )

    def test_try_variant_returns_none_never_a_half_filled_object(self):
        result = LLMGateway(providers=[], config=LLMConfig()).try_complete_structured(
            task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis
        )
        assert result is None

    def test_the_run_records_which_model_answered(self):
        response = gateway(
            [ScriptedProvider("a", ['{"qualified": true, "score": 5}'])]
        ).complete_structured(task=LLMTask.ANALYZE, system="s", prompt="p", schema=Analysis)
        assert response.run.provider_id == "a"
        assert response.run.model == "a-model"
        assert response.run.succeeded
