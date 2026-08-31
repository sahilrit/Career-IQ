# Application engine

From a scored posting to a form a human can review and submit.

```
Career Brain  ─┐
               ├─► package (resume, letter, answers, ATS report)
posting       ─┘         │
                         ▼
                    reviewer  ── fabrications? ──► withheld
                         │
                         ▼
                  open the form
                         │
              detect → map → fill → verify
                         │
                         ▼
                 FillReport ──► submission-ready, or exactly what is missing
```

## Filling is write-then-read-back

The old fill path wrapped every field in `contextlib.suppress(Exception)`. A
rejected field, an absent selector and a genuinely filled field were
indistinguishable afterwards — the failures were not loud and broken, they were
invisible. That was the single biggest cause of "filling is unreliable".

Every field now produces a `FieldResult`:

| Outcome | Meaning |
|---|---|
| `FILLED` | written and read back |
| `UNVERIFIED` | written, unreadable by design (a file input has no value) |
| `NEEDS_HUMAN` | no truthful value existed — the zero-fabrication rule working |
| `NOT_PRESENT` | not on this form |
| `FAILED` | we had a value, wrote it, and it did not take |

Read-back is what catches the dangerous case. A **disabled** input accepts a
programmatic fill and holds nothing. A **React-controlled** input accepts one
and re-renders its old value. Neither raises. Both leave a page that looks
filled and submits nothing.

Fields that legitimately reformat are not failures: a phone mask storing
`+91 91298 32709` as `091298 32709` substitutes the country code for a trunk
prefix, so the comparison is on the last nine digits.

## Blocking vs reported

`is_submittable` is false only when a **required** field failed or was left for
a human. Optional failures are still surfaced in `failures` — the fields that
most often fail are the optional EEO demographic dropdowns, and treating those
as blockers held back applications that were otherwise complete.

`submit()` refuses to click Submit on a form it knows is incomplete, and says
which field. Submitting knowingly-incomplete burns the application.

`prepare()` returns a `PreparedApplication` with `what_you_must_finish()`, so a
human reviewing gets a list rather than a screenshot to compare against their
own CV.

## Answering questions

`QuestionAnswerer` resolves a question label in this order: an answer the user
saved before, then rules over profile facts, then AI grounded strictly in those
facts. Hard facts — work authorization, visa sponsorship, demographics — are
matched by rules first so AI never fabricates them, and an unknown question
returns `answerable=False` so the field is left blank for a human.

A label CareerOS cannot read is one it must not answer. Ashby renders every
free-text question with the placeholder "Type here..." and the real question in
its `<label>`; reading the placeholder first meant the answerer was asked to
answer "Type here...", five times per form. Real labels win, and
input-describing placeholders are discarded rather than answered.

## Submit controls

A real Ashby form has **forty** `button[type=submit]` elements — every
"Upload file" control and Yes/No option is one. Matching that bare selector
picked "Upload file", so a submit click would have opened a file dialog while
believing it had applied. Submit is identified by its text; the bare type match
survives only as a last-resort fallback.

## Testing

Four levels, all real:

1. Unit — the fill contract against `FakeBrowserSession`, which can simulate a
   field that silently discards writes (`set_field_rejects`).
2. Real browser, local fixtures — `packages/careeros-autopilot/tests/ats_fixtures/`
   holds Greenhouse-, Lever-, Workable- and hostile-shaped forms served over
   `file://`. These reproduce what a fake session cannot: numeric element ids
   that are invalid CSS, a resume landing in the cover-letter file input, a
   disabled field, a controlled field that wipes its own value. Marked
   `browser`; skip with `-m "not browser"`.
3. Integration — provider → normalization → registry.
4. End-to-end against live boards:

```bash
uv run python scripts/e2e_smoke.py --per-ats 3
```

It never submits. It reports which stage each posting stops at, and exits 1 if
none reached submission-ready.
