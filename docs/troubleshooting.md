# Troubleshooting

## "AI is not configured" / everything falls back to templates

```bash
uv run python -c "
from careeros_llm import LLMGateway
for h in LLMGateway.from_env().health(): print(h.provider_id, h.status.value, h.detail)"
```

The `detail` names the fix. Common ones:

| Detail | Fix |
|---|---|
| `Not logged in · Please run /login` | run `claude`, then `/login` |
| `Please set an Auth method …` | set `GEMINI_API_KEY`, or configure `~/.gemini/settings.json` |
| `no API key configured` | set `CAREEROS_AI_API_KEY` |
| `the API key was rejected` | the key is wrong or expired |

A CLI that is installed but not logged in reports `unavailable`, not `absent`.

## A job source returns nothing

Check the board list first — a wrong slug looks exactly like an empty board on
SmartRecruiters and Workable, which answer 200 with no postings:

```bash
uv run python scripts/verify_ats_boards.py
```

`DEAD` means remove the slug. `(empty)` on a company that should have openings
means the slug is wrong.

## A search finds far too many irrelevant jobs

Use multi-word keywords. Single generic words match only the title and tags by
design; `"performance marketing"` also matches a description, `"performance"`
does not. See docs/job-providers.md.

## An application stops before submission-ready

Run the end-to-end check and read the `blocked:` line:

```bash
uv run python scripts/e2e_smoke.py --per-ats 3
```

| Blocked by | What it means |
|---|---|
| `redirects to its own careers site` | the employer has no hosted ATS form. Not fixable from here — apply on their site. |
| `a captcha challenge` / `a login/sign-in wall` | deliberately never worked around. Apply by hand. |
| `<field> (the field discarded the value…)` | the input rejected a programmatic write. The screenshot in `.careeros/screenshots/e2e/` shows the form state. |
| `<question> (no truthful value available…)` | the profile has no answer. Fill the gap in the Career Brain and it will be answered next time. |

## Browser tests are slow, or Chromium is missing

```bash
uv run playwright install chromium     # once
uv run pytest -m "not browser"         # skip the real-browser suite
```

The browser suite is skipped, not failed, when Chromium is absent.

## Tests pass on my machine and fail on someone else's

Anything asserting "no AI configured" must set `CAREEROS_LLM_CLI_ENABLED=0`;
otherwise a developer with `claude` installed gets a working provider and the
opposite result. The API suite does this automatically (`isolate_ai_providers`).
