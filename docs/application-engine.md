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

## When there is no form at all

An apply URL that serves an anti-bot challenge instead of a form is not a
detection failure. SmartRecruiters' `oneclick-ui` apply pages serve a DataDome
challenge (verified live, 2026-08-31): zero fields, zero buttons, one
`captcha-delivery.com` iframe. Reported as "no fillable form found", that sends
the user hunting for a CareerOS bug. It is detected as a captcha and reported as
"a human must apply here" — CareerOS never tries to get around one.

## Where the form is: frames

A CSS selector reaches exactly one document, so an application form rendered in
an `<iframe>` is not merely harder to find — it is **unreachable**, and looks
identical to a page with no form on it. That is what made SmartRecruiters report
"no fillable form found" on pages whose form was right there.

`BrowserSession.frame(...)` returns another `BrowserSession` scoped to a frame,
so form detection, field mapping, filling and read-back all work inside one
without knowing frames exist. `locate_form()` checks the page first (so nothing
about the other ATSes changes and no frame is enumerated on a form that is
already reachable), then each frame, and hands back a `FormLocation` carrying
both the mapping and *the session its selectors belong to* — the two are
meaningless apart.

## Which application, and whose fault

Not every posting has a form we can fill, and the reason matters:

| Route | Meaning |
|---|---|
| `ats_hosted` | the form is on the ATS's own host |
| `external` | the employer's own site, and we found a fillable form |
| `external_unsupported` | the employer takes applications elsewhere, off-ATS |
| `unknown` | we could not tell — this one counts against us |

Three of four sampled Greenhouse employers publish through Greenhouse and route
every application to their own careers site. Reporting that as "no form found"
made a working integration look broken. `PreparationResult.is_our_problem`
draws the line, and coverage numbers are reported against it.

## Answering questions

`QuestionAnswerer` resolves a question label in this order: an answer the user
saved before, then rules over profile facts, then AI grounded strictly in those
facts. Hard facts — work authorization, visa sponsorship, demographics — are
matched by rules first so AI never fabricates them.

### Confidence, and never inventing

Every answer carries a `Confidence`:

| Level | Means | Example |
|---|---|---|
| `HIGH` | copied from a verified profile fact | First name, email, current employer |
| `MEDIUM` | derived or generated from those facts | "Why do you want to work here?" |
| `LOW` | a defensible default, not a stated fact | notice period, "Open / negotiable" |
| `UNKNOWN` | cannot be answered truthfully — never sent | work authorization we do not hold |

An unanswerable question comes back as a question, not a blank: `reason` says
why, and `needs` says what would fix it ("set 'authorized to work in the US' in
your Career Brain preferences"). `answer_all()` returns the answers AND the
`UnansweredQuestion`s in one call, so it is not possible to fill a form and
quietly lose track of what was skipped. `remember_answer()` stores an answer the
user supplies so the same question is never asked twice — matched on content
words, so a rewording hits the same memory.

A label CareerOS cannot read is one it must not answer. Ashby renders every
free-text question with the placeholder "Type here..." and the real question in
its `<label>`; reading the placeholder first meant the answerer was asked to
answer "Type here...", five times per form. Real labels win, and
input-describing placeholders are discarded rather than answered.

## Submit controls

A real Ashby form has **forty** `button[type=submit]` elements — every
"Upload file" control and Yes/No option is one. Matching that bare selector
picked "Upload file", so a submit click would have opened a file dialog while
believing it had applied.

A selector cannot answer this question; only the control's *meaning* can. The
submit control is chosen by classification over real DOM signals — accessible
name, role, type, disabled state, form association, and whether it sits inside a
file-upload widget — distinguishing Upload / Continue / Next / Save / Review /
Cancel / Submit. `find_submit_control()` returns **None** rather than a best
guess when nothing has submit semantics: "no submit button" is recoverable, "we
clicked the wrong thing" is not.

The final click is re-verified at the moment it happens rather than trusting a
selector resolved earlier — a multi-step form re-renders between detection and
submission — and raises `UnsafeSubmitError` instead of clicking if the control
is now missing, disabled, or not a submit control.

## Field mapping

"First Name", "Given Name", "Legal First Name" and "Forename" are one field; so
are "Phone", "Mobile", "Telephone" and "Contact Number". A hardcoded
`input[name*='first']` matches the first and misses the rest — and matches
"First Language" by accident.

So fields are classified from every signal the DOM offers at once: `<label for>`,
a wrapping label, a label on the field *wrapper* (React form libraries),
`aria-label`, `aria-labelledby`, placeholder, `autocomplete`, `name`, `id`, input
type, and select options. Exclusion lists carry their weight: "First Language"
is not a first name, "Company Name" is an employer rather than the candidate.

Knowing what a field is FOR is not enough — how it must be written matters too.
On Greenhouse the id `cover_letter` is an `<input type="file">`, and typing into
one throws and fails the whole fill, so a purpose whose element is the wrong
kind is dropped rather than filled with the wrong interaction.

Phrases match on **word boundaries**. Plain substring matching mapped
"Race / Ethnicity" to the location field, because "city" is inside
"ethni-CITY" — the identical trap already documented in the rules-based
answerer.

### Radio and checkbox groups

Eleven EEO radio buttons are **one question with eleven options**, not eleven
questions. Each control's own label names an *option* ("Decline to
self-identify"); the question is the group's `<legend>`. Getting this wrong
produced eleven unanswerable required questions and then tried to text-fill a
radio, which raises `Input of type "radio" cannot be filled` — measured live, it
took submission-ready from 8/13 to 2/12.

Groups are collapsed by `name`, answered by clicking the matching option
(`session.choose`), and read back with `is_checked` — clicking a radio inside a
custom widget can be intercepted and do nothing, which looks identical to
success. An answer matching none of the options leaves the group alone: a wrong
EEO or work-authorization answer is worse than an unanswered one.

### One question, asked once

Two scans can reach the same widget through different elements and produce
different selectors for it. On a live Greenhouse form "How did you hear about
this job?" was answered twice — once by opening its react-select, once by
typing into the inner input, which silently discarded the value and then
reported a failure on a question that had already been answered correctly.
Questions are therefore deduplicated by **label** as well as by selector, and
the dropdown interaction wins.

## Readiness, not "ready"

"Application failed." tells the user nothing. Every attempt produces an
`ApplicationReadiness`: a per-stage checklist, a score computed from it, the
questions returned to the user with their reasons, and an `Evidence` record.

```
Application readiness: 92%

✓ Job identified
✓ Application URL found
...
⚠ Questions answered — 1 left for you
```

`failure_report()` is the whole message — what happened, why, what was
completed, what remains, and who must act. Evidence keeps the posting URL, the
application URL, the ATS, the route, the fields detected/mapped/unmapped, the
validation outcome and any screenshot — and deliberately keeps **field names,
never field values**, so it is safe to attach to a bug report rather than being
a copy of the user's profile.

## Testing

Four levels, all real:

1. Unit — the fill contract against `FakeBrowserSession`, which can simulate a
   field that silently discards writes (`set_field_rejects`).
2. Real browser, local fixtures — `packages/careeros-autopilot/tests/ats_fixtures/`
   holds Greenhouse-, Lever-, Workable-, SmartRecruiters-(iframe) and
   hostile-shaped forms served over `file://`. These reproduce what a fake session cannot: numeric element ids
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
