# Career profile

`careeros_career_brain.CareerBrain` is the single authority on what is true
about the user. Nothing else may invent a fact about them.

Holds: identity and contact details, links, preferences (titles, locations,
remote, salary, employment types), work authorization and visa sponsorship
answers, saved screening answers, experiences with achievements and metrics,
projects, education, certifications, skills, languages, awards, plus the CRM
side (companies, recruiters, applications).

## The zero-fabrication rule

AI may **rewrite and select from** these facts. It may not manufacture them.

Two mechanisms enforce it rather than merely asking for it:

1. **Answering.** Work authorization and visa sponsorship come from stored
   booleans; when unknown the answerer returns `answerable=False` and the field
   is left blank. A wrong visa answer is far worse than an unanswered one.
2. **Reviewing.** Generated prose is checked back against the brain before it
   reaches an employer — see below.

## The reviewer

`careeros_application_engine.review` runs two layers.

**Deterministic**, needing no AI and unable to hallucinate:

- employers named in the draft that appear nowhere in the profile
- figures quoted that appear nowhere in the profile
- degrees claimed with no matching education record
- template placeholders (`[Company Name]`, `{{role}}`, `XX years`, `TODO`)

The employer being applied to and the candidate's own name are passed as
`allowed_extra`, since a letter naming its recipient is correct.

**AI**, routed as `LLMTask.REVIEW` so it prefers a different provider than the
drafter. It is asked to find problems, never to approve — "looks good" parses to
nothing rather than to an endorsement.

`ApplicationPackage.is_safe_to_send` is `False` for an **unreviewed** package.
Absence of findings and absence of checking must not look the same to a caller.
