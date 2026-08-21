"""Drafting for networking outreach — grounded in the Career Brain and the
contact. Deterministic templates are the free tier; the API optionally has an
LLM rewrite them. No fabricated facts either way."""

from __future__ import annotations

from careeros_career_brain import CareerBrain
from careeros_crm import Contact

KINDS = ("intro", "referral", "thank_you")

_LABELS = {"intro": "introduction", "referral": "referral", "thank_you": "thank-you"}


def _first_name(full_name: str) -> str:
    return full_name.split()[0] if full_name.strip() else "there"


def draft_outreach(
    *, kind: str, contact: Contact, brain: CareerBrain | None, target_role: str = ""
) -> tuple[str, str]:
    """Return (subject, body) for the given outreach kind."""
    me = brain.identity.full_name if brain else "me"
    headline = brain.identity.headline if brain and brain.identity.headline else ""
    who = _first_name(contact.name)
    org = contact.organization_name or "your team"
    role = target_role or "a role that fits"
    intro_line = f"I'm {me}" + (f", {headline}" if headline else "") + "."

    if kind == "referral":
        subject = f"Referral for {target_role or 'an open role'} at {org}?"
        body = (
            f"Hi {who},\n\n"
            f"{intro_line} I'm exploring {role} at {org} and your name came up as "
            f"someone who'd know the team well.\n\n"
            f"Would you be open to a quick referral or a 15-minute chat about what they're "
            f"looking for? Happy to share my background so it's easy to point me the right way.\n\n"
            f"Thanks so much,\n{me}"
        )
    elif kind == "thank_you":
        subject = f"Thank you, {who}"
        body = (
            f"Hi {who},\n\n"
            f"Thank you for taking the time to talk today — I really valued your perspective "
            f"on {org}. It gave me a much clearer picture of the work and the team.\n\n"
            f"I'd love to stay in touch, and please let me know if there's anything I can do "
            f"for you in return.\n\n"
            f"Best,\n{me}"
        )
    else:  # intro
        subject = f"Quick hello from {me}"
        body = (
            f"Hi {who},\n\n"
            f"{intro_line} I came across your work at {org} and wanted to reach out and "
            f"connect.\n\n"
            f"I'm always keen to learn from people building interesting things — would you be "
            f"open to a brief chat sometime?\n\n"
            f"Best,\n{me}"
        )
    return subject, body


def ai_prompt(*, kind: str, contact: Contact, brain: CareerBrain | None, target_role: str) -> str:
    facts = []
    if brain:
        facts.append(f"My name: {brain.identity.full_name}")
        if brain.identity.headline:
            facts.append(f"My headline: {brain.identity.headline}")
        if brain.identity.summary:
            facts.append(f"My summary: {brain.identity.summary}")
        skills = ", ".join(skill.name for skill in brain.skills[:8])
        if skills:
            facts.append(f"My top skills: {skills}")
    facts.append(f"Contact: {contact.name} at {contact.organization_name or 'their company'}")
    if target_role:
        facts.append(f"Target role I'm interested in: {target_role}")
    joined = "\n".join(facts)
    return (
        f"Write a short, warm {_LABELS.get(kind, 'outreach')} email (5-8 sentences, no "
        f"placeholders). Use only these facts:\n{joined}\n\n"
        "Return the email body only, starting with the greeting."
    )


AI_SYSTEM = (
    "You write concise, genuine networking emails for a job seeker. Warm, specific, "
    "never salesy. Use only the facts provided — never invent employers, titles, or metrics."
)
