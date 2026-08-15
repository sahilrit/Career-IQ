"""Security policy: a configurable, testable password/session policy —
distinct from Phase 26's SecretCipher (encryption of stored secrets)
and Phase 21's agent authorization (what an agent may do). This is
about what a human account must satisfy to be considered compliant.
"""

from __future__ import annotations

from pydantic import BaseModel


class SecurityPolicy(BaseModel):
    min_length: int = 12
    require_uppercase: bool = True
    require_digit: bool = True
    require_symbol: bool = True
    session_timeout_minutes: int = 60
    mfa_required: bool = False


_SYMBOLS = set("!@#$%^&*()-_=+[]{};:,.<>/?")


def check_password(password: str, policy: SecurityPolicy) -> list[str]:
    violations = []
    if len(password) < policy.min_length:
        violations.append(f"must be at least {policy.min_length} characters")
    if policy.require_uppercase and not any(char.isupper() for char in password):
        violations.append("must contain an uppercase letter")
    if policy.require_digit and not any(char.isdigit() for char in password):
        violations.append("must contain a digit")
    if policy.require_symbol and not any(char in _SYMBOLS for char in password):
        violations.append("must contain a symbol")
    return violations
