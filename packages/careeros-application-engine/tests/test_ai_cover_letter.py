from careeros_application_engine import AICoverLetterGenerator
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_job_providers import JobPosting


class FakeClient:
    def __init__(self):
        self.calls = []

    def complete(self, *, system, prompt):
        self.calls.append((system, prompt))
        return "AI cover letter."


def _brain():
    return CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="a@x.com", summary="Growth marketer."),
        skills=[Skill(name="Meta Ads")],
    )


def _posting():
    return JobPosting(
        source_provider="test",
        external_id="1",
        title="PPC Manager",
        company_name="Acme",
        url="https://acme.com/j/1",
        description="Run paid campaigns.",
    )


def test_uses_ai_and_grounds_prompt_in_brain():
    fake = FakeClient()
    out = AICoverLetterGenerator(fake).generate(_brain(), _posting())
    assert out == "AI cover letter.\n"
    system, prompt = fake.calls[0]
    assert "never invent" in system.lower()
    assert "Ada Lovelace" in prompt
    assert "Meta Ads" in prompt
    assert "Acme" in prompt
