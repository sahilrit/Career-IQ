# Testing

```bash
uv run pytest                     # everything (~5 min; includes a real browser)
uv run pytest -m "not browser"    # fast suite (~3 min)
uv run pytest packages/careeros-llm
```

## Levels

**1 — Unit.** Pure logic: normalization, matching, filtering, the fill contract.
Browser work uses `FakeBrowserSession`, which can simulate the failures that
matter (`set_field_rejects` makes a field silently discard writes, exactly as a
disabled or React-controlled input does).

**2 — Integration.** Provider → normalization → registry, and profile → package
→ review. No network: adapters are exercised against recorded payload shapes.

**3 — Real browser, local fixtures.** `packages/careeros-autopilot/tests/ats_fixtures/`
holds Greenhouse-, Lever-, Workable- and hostile-shaped forms served over
`file://`. Real Chromium, no network, so no company can break the suite by
editing its careers page. This is the only place DOM-level failures reproduce.
Marked `browser`.

**4 — End-to-end, live.** `scripts/e2e_smoke.py` runs the real workflow against
live boards and real forms, and reports the stage each posting reached. It never
submits. Exit 1 if none reached submission-ready.

**5 — Board health.** `scripts/verify_ats_boards.py` probes every configured
company board.

## Rules

- **No fabricated results.** No `mock_success()`, no test that passes by
  bypassing the thing it names. If something does not work, the test says so.
- **Hermetic.** A test must not depend on what is installed on the machine
  running it. Anything about AI availability pins `CAREEROS_LLM_CLI_ENABLED`.
- **Test the failure.** Every non-obvious defensive branch has a test naming the
  real failure it prevents — the disabled input, the numeric element id, the
  200-with-empty-board, the phone mask, the forty submit buttons.
