"""LLM scoring: one structured call that corrects, summarises, and scores.

The heuristic scorer in ``scoring`` stays as the cheap first pass — it is
arithmetic over the Career Brain and costs nothing. This runs on what
clears it, and does three jobs in a single request:

1. **Job fact review.** Scraped postings are lossy: a salary in the prose
   that never made it into a structured field, a remote role we recorded
   as onsite. The model proposes corrections to a whitelist of fields,
   each one requiring a verbatim excerpt from the posting.
2. **Job brief.** A neutral summary of what the role actually is, with
   the employer's marketing language stripped out.
3. **Candidate evaluation.** A 0-100 fit score with a short reason.

The interesting part is how little of the answer is taken on trust. The
model is asked for evidence and then the evidence is *checked* — a patch
whose supporting quote does not appear in the posting is dropped, which
is what stops a confident hallucination from rewriting a salary. Low
confidence is dropped outright; medium may only fill a value we are
missing, never overwrite one we scraped.

The AI client is structural: anything with ``complete(system=, prompt=)``
works, so this module needs no dependency on ``careeros_ai``.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from careeros_common import get_logger
from careeros_job_providers import EmploymentType, JobPosting, Salary

logger = get_logger(__name__)

#: Fields the model may propose corrections to. Deliberately excludes
#: ``url``, ``external_id`` and ``source_provider``: those are identity, and
#: a model that could rewrite them could repoint an application at anything.
PATCHABLE_FIELDS: tuple[str, ...] = (
    "title",
    "company_name",
    "location",
    "remote",
    "salary_min",
    "salary_max",
    "salary_currency",
    "salary_period",
    "employment_type",
)

Confidence = Literal["high", "medium", "low"]

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)
_WS_RE = re.compile(r"\s+")

DEFAULT_MAX_DESCRIPTION_CHARS = 8_000


class AICompleter(Protocol):
    def complete(self, *, system: str, prompt: str) -> str: ...


class JobBrief(BaseModel):
    """A neutral read of the posting, with employer fluff removed."""

    role_summary: str = ""
    they_want: list[str] = Field(default_factory=list)
    specifics: list[str] = Field(default_factory=list)
    company_offers: list[str] = Field(default_factory=list)
    practical_details: list[str] = Field(default_factory=list)
    missing_or_unclear: list[str] = Field(default_factory=list)
    repeated_signals: list[str] = Field(default_factory=list)


class JobFactPatch(BaseModel):
    field: str
    value: str | int | float | bool
    confidence: Confidence
    evidence: str


class LlmScoreResult(BaseModel):
    score: int
    reason: str = ""
    brief: JobBrief | None = None
    #: Only patches that survived evidence and confidence checks.
    patches: list[JobFactPatch] = Field(default_factory=list)
    #: Things the model flagged, plus anything we rejected and why.
    warnings: list[str] = Field(default_factory=list)


# --- prompt ------------------------------------------------------------------

_SYSTEM_PROMPT_TEMPLATE = """You assess job postings for a specific candidate.

Do three things in one response:

1. JOB FACT REVIEW — candidate-independent. Compare the structured JOB DATA
   with the POSTING TEXT. Propose a patch only where a whitelisted field is
   missing or clearly wrong, and only with an exact supporting excerpt copied
   verbatim from the POSTING TEXT. Never guess, never infer from general
   knowledge, never annualise or convert a figure, never paraphrase the
   evidence. Use "high" only for an unambiguous correction; "medium" may only
   fill a value that is currently missing; omit anything ambiguous.

2. JOB BRIEF — use only what the posting states. Stay neutral, strip employer
   marketing language, and never judge the candidate. Use "Not stated" where a
   practical detail is absent.

3. CANDIDATE EVALUATION — score 0-100 for how well this candidate fits, with a
   one or two sentence reason.

Put anything you cannot represent safely — a contradiction, a distinction the
fields cannot capture — into "warnings" rather than forcing a patch.

Respond with ONLY valid JSON, no prose and no code fences:
{"score": <int 0-100>, "reason": "<string>",
 "brief": {"role_summary": "<string>", "they_want": [], "specifics": [],
           "company_offers": [], "practical_details": [],
           "missing_or_unclear": [], "repeated_signals": []},
 "patches": [{"field": "<one of: __FIELDS__>", "value": <string|number|boolean>,
              "confidence": "high|medium|low", "evidence": "<verbatim excerpt>"}],
 "warnings": []}"""

# The prompt is a JSON template, so it is riddled with braces an f-string would
# need doubled. A placeholder swap keeps the literal readable.
SYSTEM_PROMPT = _SYSTEM_PROMPT_TEMPLATE.replace("__FIELDS__", ", ".join(PATCHABLE_FIELDS))


def build_prompt(
    posting: JobPosting,
    *,
    profile_summary: str,
    max_description_chars: int = DEFAULT_MAX_DESCRIPTION_CHARS,
) -> str:
    description = posting.description or ""
    if len(description) > max_description_chars:
        description = description[:max_description_chars] + "\n…[truncated]"

    job_data = {
        "title": posting.title,
        "company_name": posting.company_name,
        "location": posting.location,
        "remote": posting.remote,
        "salary_min": posting.salary.min_amount if posting.salary else None,
        "salary_max": posting.salary.max_amount if posting.salary else None,
        "salary_currency": posting.salary.currency if posting.salary else None,
        "salary_period": posting.salary.period if posting.salary else None,
        "employment_type": posting.employment_type.value if posting.employment_type else None,
        "tags": posting.tags,
    }

    return (
        f"CANDIDATE PROFILE:\n{profile_summary}\n\n"
        f"JOB DATA (what we scraped):\n{json.dumps(job_data, indent=2)}\n\n"
        f"POSTING TEXT:\n{description}"
    )


# --- parsing -----------------------------------------------------------------


def _extract_json(raw: str) -> dict[str, Any]:
    """Pull the JSON object out of a completion.

    Models wrap JSON in code fences and top-and-tail it with commentary
    however firmly you ask them not to, so strip fences first and then fall
    back to the outermost braces.
    """
    text = _FENCE_RE.sub("", raw).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("no JSON object found in the model's response") from None
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"model response was not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("model response was not a JSON object")
    return parsed


def _normalized(text: str) -> str:
    return _WS_RE.sub(" ", text).strip().lower()


def _evidence_supports(evidence: str, posting: JobPosting) -> bool:
    """Is this quote actually in the posting?

    Compared with whitespace collapsed and case folded, because models
    reflow and recapitalise text they copy. Anything shorter than a few
    characters is not evidence of anything.
    """
    quote = _normalized(evidence)
    if len(quote) < 8:
        return False
    haystack = _normalized(f"{posting.title} {posting.company_name} {posting.description}")
    return quote in haystack


def _current_value(posting: JobPosting, field: str) -> Any:
    if field == "salary_min":
        return posting.salary.min_amount if posting.salary else None
    if field == "salary_max":
        return posting.salary.max_amount if posting.salary else None
    if field == "salary_currency":
        return posting.salary.currency if posting.salary else None
    if field == "salary_period":
        return posting.salary.period if posting.salary else None
    if field == "employment_type":
        return posting.employment_type.value if posting.employment_type else None
    return getattr(posting, field, None)


def _vet_patch(
    raw: dict[str, Any], posting: JobPosting, warnings: list[str]
) -> JobFactPatch | None:
    field = str(raw.get("field") or "")
    if field not in PATCHABLE_FIELDS:
        warnings.append(f"ignored a correction to '{field}': not a patchable field")
        return None

    confidence = str(raw.get("confidence") or "").lower()
    if confidence not in ("high", "medium"):
        return None

    value = raw.get("value")
    if value is None or isinstance(value, list | dict):
        return None

    evidence = str(raw.get("evidence") or "")
    if not _evidence_supports(evidence, posting):
        warnings.append(
            f"ignored a correction to '{field}': its evidence does not appear in the posting"
        )
        return None

    # Medium confidence may add what we're missing, never overwrite what we have.
    if confidence == "medium" and _current_value(posting, field) not in (None, ""):
        return None

    return JobFactPatch(
        field=field,
        value=value,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        evidence=evidence,
    )


def parse_scoring_response(raw: str, *, posting: JobPosting) -> LlmScoreResult:
    """Turn a completion into a vetted result, or raise if it is unusable."""
    payload = _extract_json(raw)

    score_raw = payload.get("score")
    if isinstance(score_raw, bool) or not isinstance(score_raw, int | float):
        raise ValueError(f"score was not a number: {score_raw!r}")
    score = max(0, min(100, int(score_raw)))

    warnings = [str(w) for w in (payload.get("warnings") or []) if str(w).strip()]

    brief = None
    brief_raw = payload.get("brief")
    if isinstance(brief_raw, dict):
        try:
            brief = JobBrief.model_validate(brief_raw)
        except Exception:
            warnings.append("the job brief was malformed and has been dropped")

    patches: list[JobFactPatch] = []
    for raw_patch in payload.get("patches") or []:
        if not isinstance(raw_patch, dict):
            continue
        vetted = _vet_patch(raw_patch, posting, warnings)
        if vetted is not None:
            patches.append(vetted)

    return LlmScoreResult(
        score=score,
        reason=str(payload.get("reason") or ""),
        brief=brief,
        patches=patches,
        warnings=warnings,
    )


# --- applying ----------------------------------------------------------------

#: Currency markers we can read straight out of a supporting excerpt.
_CURRENCY_MARKERS: tuple[tuple[str, str], ...] = (
    ("£", "GBP"),
    ("gbp", "GBP"),
    ("€", "EUR"),
    ("eur", "EUR"),
    ("₹", "INR"),
    ("inr", "INR"),
    ("rs.", "INR"),
    ("$", "USD"),
    ("usd", "USD"),
    ("cad", "CAD"),
    ("aud", "AUD"),
    ("chf", "CHF"),
    ("sgd", "SGD"),
)

_AMOUNT_FIELDS = ("salary_min", "salary_max")

_SALARY_FIELDS = {
    "salary_min": "min_amount",
    "salary_max": "max_amount",
    "salary_currency": "currency",
    "salary_period": "period",
}


def _currency_from_evidence(patches: list[JobFactPatch]) -> str | None:
    """Read the currency off the excerpts that justified the amounts.

    A figure the model lifted from "£55,000 to £70,000" carries its currency
    in the same sentence, so there is no need to guess.
    """
    text = " ".join(p.evidence for p in patches if p.field in _AMOUNT_FIELDS).lower()
    for marker, code in _CURRENCY_MARKERS:
        if marker in text:
            return code
    return None


def apply_patches(posting: JobPosting, patches: list[JobFactPatch]) -> JobPosting:
    """A copy of ``posting`` with the vetted corrections applied.

    Never mutates the original — a posting is cached at discovery time and
    read back later, so an in-place edit would rewrite history.
    """
    if not patches:
        return posting

    updates: dict[str, Any] = {}
    salary_updates: dict[str, Any] = {}

    for patch in patches:
        if patch.field in _SALARY_FIELDS:
            salary_updates[_SALARY_FIELDS[patch.field]] = patch.value
        elif patch.field == "remote":
            updates["remote"] = bool(patch.value)
        elif patch.field == "employment_type":
            try:
                updates["employment_type"] = EmploymentType(str(patch.value).lower())
            except ValueError:
                logger.debug("Skipped an unmappable employment_type patch: %r", patch.value)
        else:
            updates[patch.field] = str(patch.value)

    if salary_updates:
        base = posting.salary.model_dump() if posting.salary else {}
        base.update(salary_updates)

        # A brand-new salary needs a currency we can actually justify. The
        # model's default would be whatever Salary declares, which turns a
        # GBP advert into dollars — a number that looks precise and is wrong
        # by an exchange rate. Explicit patch first, then the evidence, then
        # give up on the amounts entirely.
        if posting.salary is None and "currency" not in salary_updates:
            inferred = _currency_from_evidence(patches)
            if inferred is None:
                logger.debug("Dropped a salary patch with no determinable currency")
                salary_updates = {}
            else:
                base["currency"] = inferred

        if salary_updates:
            try:
                updates["salary"] = Salary.model_validate(base)
            except Exception:
                logger.debug("Skipped an unmappable salary patch: %r", salary_updates)

    return posting.model_copy(update=updates)


# --- the scorer --------------------------------------------------------------


class LlmJobScorer:
    """Scores one posting per call. Returns ``None`` rather than raising.

    Discovery must survive a flaky model: a scoring failure costs us the
    richer score for that posting, and nothing else.
    """

    def __init__(
        self,
        client: AICompleter,
        *,
        max_description_chars: int = DEFAULT_MAX_DESCRIPTION_CHARS,
    ) -> None:
        self._client = client
        self._max_description_chars = max_description_chars

    def score(self, posting: JobPosting, *, profile_summary: str) -> LlmScoreResult | None:
        prompt = build_prompt(
            posting,
            profile_summary=profile_summary,
            max_description_chars=self._max_description_chars,
        )
        try:
            raw = self._client.complete(system=SYSTEM_PROMPT, prompt=prompt)
        except Exception as exc:
            logger.warning("LLM scoring failed for %s: %s", posting.url, exc)
            return None

        try:
            return parse_scoring_response(raw, posting=posting)
        except ValueError as exc:
            logger.warning("LLM scoring returned unusable output for %s: %s", posting.url, exc)
            return None
