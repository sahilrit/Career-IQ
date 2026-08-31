"""Turning model prose into a validated object.

Anywhere CareerOS needs a machine-readable answer — a job analysis, a
classified application question, a set of reviewer findings, a score — free
text is the wrong contract. A model that returns "I'd say roughly 7 out of 10"
where a float was expected does not fail loudly; it fails three functions
later, in code that has no idea an LLM was involved.

So the shape is declared as a Pydantic model, the model is told exactly what
JSON to produce, and the output is parsed and validated before any caller sees
it. Output that does not validate is a ``MalformedResponseError`` — which the
gateway treats as retryable, because re-asking with the validation error
quoted back is the one repair that reliably works.
"""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

#: ```json … ``` fences, which several models add no matter how firmly asked.
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)


def schema_instruction(schema: type[BaseModel]) -> str:
    """The instruction appended to a system prompt to pin the output shape.

    The JSON Schema is included verbatim rather than paraphrased: it is what
    validation will actually enforce, so anything softer here is a promise the
    validator will not keep.
    """
    return (
        "\n\nRespond with a single JSON object and NOTHING else — no prose, no "
        "explanation, no markdown fences. It must validate against this JSON Schema:\n"
        f"{json.dumps(schema.model_json_schema(), indent=2)}\n"
        "If you do not know a value, use the schema's null/empty option rather than "
        "inventing one. Never guess a fact about the candidate."
    )


def extract_json(text: str) -> Any:
    """The JSON value inside ``text``, however the model wrapped it.

    Tolerant about packaging (fences, a leading sentence) and strict about
    content: it never repairs malformed JSON, because a "fixed" object is a
    guess about what the model meant, and guessing is the failure mode this
    whole layer exists to remove.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("the response was empty")

    fenced = _FENCE_RE.search(raw)
    if fenced:
        raw = fenced.group(1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # A model that prefixed its object with a sentence. Take the outermost
    # brace/bracket span and try that — but only that; no cleverer surgery.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        end = raw.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("the response did not contain a JSON object")


def parse_structured[V: BaseModel](text: str, schema: type[V]) -> V:
    """``text`` as a validated ``schema`` instance.

    Raises ``ValueError`` with a message written to be handed straight back to
    the model as a repair instruction — which is exactly what the gateway does
    with it.
    """
    try:
        payload = extract_json(text)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"the response was a JSON {type(payload).__name__}, not the required object"
        )
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in error['loc']) or '(root)'}: {error['msg']}"
            for error in exc.errors()[:6]
        )
        raise ValueError(f"the JSON did not match the schema — {problems}") from exc


def repair_prompt(original_prompt: str, bad_output: str, problem: str) -> str:
    """A second ask that quotes back what was wrong.

    Short on purpose: the model already has the schema in its system prompt,
    so what it is missing is the specific defect, not another copy of the
    requirements.
    """
    return (
        f"{original_prompt}\n\n"
        "--- YOUR PREVIOUS ANSWER WAS REJECTED ---\n"
        f"You replied:\n{bad_output[:1500]}\n\n"
        f"That was rejected because: {problem}\n"
        "Reply again with ONLY the corrected JSON object."
    )
