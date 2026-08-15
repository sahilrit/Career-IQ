"""Cold outreach generation: deterministic and template-based (no LLM
required), referencing only what the audit actually found about the
company and the user's own real top skills — nothing about either side
is invented.
"""

from __future__ import annotations

from typing import Protocol

from careeros_career_brain import CareerBrain
from careeros_client_acquisition.audit import AuditReport
from careeros_client_acquisition.company import Company

_TEMPLATE = """Hi{greeting_name},

I came across {company_name} and noticed {issue_sentence}

{value_prop}

Would you be open to a quick call to see if it's worth fixing?

Best,
{full_name}
"""


class OutreachGenerator(Protocol):
    def generate(self, brain: CareerBrain, company: Company, report: AuditReport) -> str: ...


class TemplateOutreachGenerator:
    def generate(self, brain: CareerBrain, company: Company, report: AuditReport) -> str:
        greeting_name = f" {company.contact_name}" if company.contact_name else ""
        rendered = _TEMPLATE.format(
            greeting_name=greeting_name,
            company_name=company.name,
            issue_sentence=self._issue_sentence(report),
            value_prop=self._value_prop(brain),
            full_name=brain.identity.full_name,
        )
        return rendered.strip() + "\n"

    def _issue_sentence(self, report: AuditReport) -> str:
        if not report.findings:
            return "a couple of things worth a second look on the site."
        top = report.findings[0]
        return f"{top.detail}."

    def _value_prop(self, brain: CareerBrain) -> str:
        skill_names = [skill.name for skill in brain.skills[:3]]
        if skill_names:
            skills = ", ".join(skill_names)
            return f"I help companies fix issues like this — my background is in {skills}."
        return "I help companies fix issues like this."
