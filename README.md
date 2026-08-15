# CareerOS

A general-purpose, multi-tenant **AI Career Operating System** — an AI
personal career agency, built as a platform rather than a single app.

**Core principle:** build the platform once. Job boards, freelance
platforms, AI capabilities, workflows, agents, and integrations are all
replaceable.

**Critical constraint:** no mandatory paid API keys. The core platform is
buildable and runnable end-to-end using free/open-source/local software,
browser automation, public web data, and user-provided credentials/OAuth
where appropriate — paid providers are optional plugins, never a
dependency of the core.

## Status

🚧 Phase 22 of 60 — Autonomous Application Execution. The full loop
works today, for both employment and freelance opportunities: postings
are discovered (RemoteOK, Fiverr), normalized, and scored against a
Career Brain profile; qualified opportunities get a real resume/cover-
letter/answers/proposal package generated (nothing fabricated); an
authorization system decides whether to act (MANUAL/SUPERVISED/
FULL_AUTONOMOUS, with financial/legal/identity actions always requiring
a human, in every mode); and a Playwright-backed browser runner submits
the package through an actual web form — with retries, screenshots,
pacing, and a human-takeover path for captchas, unexpected pages, or
failed submissions. No arbitrary cap on how many qualified applications
one run processes. See [`docs/phases/ROADMAP.md`](docs/phases/ROADMAP.md)
for the full plan and [`docs/architecture/overview.md`](docs/architecture/overview.md)
for what's built so far.

## Repository layout

```
careeros/
├── packages/                                # uv workspace members
│   ├── careeros-common/                     # config, logging, exceptions, DocumentStore
│   ├── careeros-career-brain/               # authoritative domain models + repository
│   ├── careeros-plugin-sdk/                 # plugin interface, manifest, registry
│   ├── careeros-event-bus/                  # in-process pub/sub
│   ├── careeros-memory/                     # working memory, history, analytics, semantic search
│   ├── careeros-job-providers/              # FIND_JOBS provider SDK
│   ├── careeros-remoteok-provider/          # the reference job provider (RemoteOK)
│   ├── careeros-job-discovery/              # discover -> score -> store -> emit pipeline
│   ├── careeros-runtime/                    # worker pool, scheduler, lifecycle
│   ├── careeros-job-agent/                  # autonomous discovery + qualification loop
│   ├── careeros-career-brain-engine/        # profile matching, recommendations
│   ├── careeros-application-engine/         # resume/cover letter/answers/ATS generation
│   ├── careeros-browser/                    # BrowserSession abstraction (Playwright)
│   ├── careeros-application-runner/         # submits an application via a real browser
│   ├── careeros-cli/                        # the `careeros` command-line interface
│   ├── careeros-application-intelligence/   # apply decisions, safeguards, outcomes
│   ├── careeros-human-in-the-loop/          # problem detection + AI/human handoff
│   ├── careeros-freelance-providers/        # FIND_GIGS provider SDK
│   ├── careeros-fiverr-provider/            # a second FIND_GIGS provider (browser-driven)
│   ├── careeros-opportunity-intelligence/   # unifies employment + freelance, CRM, proposals
│   ├── careeros-autonomy/                   # risk-based authorization, decision memory, pacing
│   └── careeros-autonomous-execution/       # the full autonomous apply loop
├── config/                         # layered YAML configuration (default/dev/test/prod/local)
├── docs/
│   ├── architecture/                # current-state architecture docs
│   ├── development/                 # setup + coding standards
│   └── phases/                      # the roadmap and per-phase notes
└── pyproject.toml                  # workspace root (virtual — not itself installed)
```

## Getting started

```bash
uv sync --all-packages
uv run pre-commit install
uv run pytest
```

See [`docs/development/setup.md`](docs/development/setup.md) for the full
developer workflow and [`docs/development/standards.md`](docs/development/standards.md)
for the rules every package follows.

## License

Not yet decided.
