"""Evidence has to be safe to attach to a bug report.

A failed application that cannot be reproduced is a bug report with no repro
steps — so every attempt keeps an evidence record. The cost of getting that
wrong is that every debug log becomes a copy of the user's profile, so the
record carries field NAMES and never field VALUES, and never a credential.
"""

from __future__ import annotations

from careeros_application_runner import FieldOutcome, FieldResult, FillReport, FormFieldMapping
from careeros_autopilot import ApplicationRoute
from careeros_autopilot.readiness import assess_readiness
from careeros_llm import LLMRun, LLMTask

SECRETS = [
    "ada@example.com",
    "+44 20 7946 0000",
    "Dear Acme, I would love to work on growth.",
    "sk-ant-api03-super-secret",
    "cf_clearance=abcdef",
]


def report_with_personal_data() -> FillReport:
    report = FillReport()
    report.add(
        FieldResult(field="email", selector="#email", outcome=FieldOutcome.FILLED, required=True)
    )
    report.add(FieldResult(field="phone", selector="#phone", outcome=FieldOutcome.FILLED))
    report.add(
        FieldResult(
            field="cover_letter",
            selector="#cl",
            outcome=FieldOutcome.NOT_PRESENT,
            detail="no selector for this field on this form",
        )
    )
    return report


class TestEvidenceCarriesNoSecrets:
    def test_no_profile_value_reaches_the_evidence_record(self):
        readiness = assess_readiness(
            posting_url="https://boards.greenhouse.io/acme/jobs/1",
            application_url="https://boards.greenhouse.io/acme/jobs/1",
            ats="greenhouse",
            route=ApplicationRoute.ATS_HOSTED,
            mapping=FormFieldMapping(
                email_selector="#email", submit_selector="#go", success_selector="#done"
            ),
            fill_report=report_with_personal_data(),
            cover_letter="Dear Acme, I would love to work on growth.",
        )
        blob = repr(readiness.evidence.as_dict())
        for secret in SECRETS:
            assert secret not in blob, secret

    def test_field_names_ARE_kept_because_they_are_what_explain_a_failure(self):
        readiness = assess_readiness(
            posting_url="https://x.test/1", fill_report=report_with_personal_data()
        )
        evidence = readiness.evidence
        assert "email" in evidence.detected_fields
        assert "cover_letter" in evidence.unmapped_fields

    def test_the_record_is_json_serialisable_so_it_can_be_stored_or_attached(self):
        import json

        readiness = assess_readiness(posting_url="https://x.test/1")
        assert json.loads(json.dumps(readiness.evidence.as_dict()))

    def test_the_reports_a_human_reads_carry_no_credentials_either(self):
        readiness = assess_readiness(
            posting_url="https://x.test/1",
            fill_report=report_with_personal_data(),
            cover_letter="Dear Acme, I would love to work on growth.",
        )
        for text in (readiness.report(), readiness.failure_report()):
            assert "sk-ant" not in text
            assert "cf_clearance" not in text


class TestLLMProvenanceCarriesNoPrompt:
    def test_a_run_record_has_no_field_that_could_hold_the_prompt(self):
        # The prompt contains the candidate's whole profile. The run record is
        # stored alongside applications, so it must record WHICH model spoke
        # and nothing about what it was told.
        fields = set(LLMRun.model_fields)
        assert not fields & {"prompt", "system", "text", "response", "output", "messages"}

    def test_it_records_length_rather_than_content(self):
        run = LLMRun(
            task=LLMTask.WRITE,
            provider_id="anthropic",
            model="m",
            succeeded=True,
            response_chars=1234,
        )
        assert run.response_chars == 1234
        assert "1234" in repr(run)
        # And there is nowhere for the text itself to live.
        assert "response_text" not in LLMRun.model_fields
