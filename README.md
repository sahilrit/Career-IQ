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

🚧 Phase 49 of 60 — AI Skill Marketplace. The full autonomous apply loop
works today, for both employment and freelance opportunities: postings
are discovered (RemoteOK, Fiverr), scored against a Career Brain
profile, turned into a real application package (nothing fabricated),
authorized (MANUAL/SUPERVISED/FULL_AUTONOMOUS, with financial/legal/
identity actions always requiring a human), and submitted through an
actual web form via Playwright. On the freelance side it discovers and
audits prospective clients, generates every pitch deliverable, tracks
contacts through a relationship timeline, and turns projects into
public content. Beyond landing the work: offers get evaluated into one
comparable Opportunity Value; clients get tracked through a computed
lifecycle stage; income feeds a full-time-vs-freelance strategy
comparison; company signals predict demand before a posting exists;
A/B experiments and a Career Intelligence Engine learn what works; and
a CEO Agent allocates effort across the four divisions as real results
come in. Users can build no-code WHEN/THEN automations. The product has
a UI (Streamlit dashboard: overview, opportunities, Career Brain
manager) and an analytics layer with a transparent Career ROI
breakdown. Security: a general-purpose audit log, consent management,
data export/deletion, rate limiting, and a failure queue with recovery
(tenancy, encryption, and agent authorization already existed). The
zero-cost constraint is now an explicit, tested guarantee, the platform
is packaged for local/Docker self-hosting, and a Plugin Marketplace
(Integrations) plus AI Skill Marketplace now exist — both honestly
distinguishing what's actually built from what's roadmap-only. No
arbitrary cap on how many qualified applications one run processes.
See [`docs/phases/ROADMAP.md`](docs/phases/ROADMAP.md) for the full
plan and [`docs/architecture/overview.md`](docs/architecture/overview.md)
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
│   ├── careeros-autonomous-execution/       # the full autonomous apply loop
│   ├── careeros-core/                       # platform-wide contracts (registry, health, events)
│   ├── careeros-capability-marketplace/     # ranked provider registration + fallback
│   ├── careeros-tenancy/                    # multi-tenant identity + tenant-scoped storage
│   ├── careeros-credentials/                # encrypted credential vault, audit log, OAuth
│   ├── careeros-communication-intelligence/ # classifies inbound recruiter/interviewer email
│   ├── careeros-calendar-assistant/         # email -> interview calendar events + workspace
│   ├── careeros-interview-intelligence/     # company research, questions, briefing schedule
│   ├── careeros-employment-division/        # full pipeline orchestration + progress tracking
│   ├── careeros-client-acquisition/         # freelance-side pipeline: discovery -> client
│   ├── careeros-audit-proposal-engine/      # Shopify/Meta Ads audits, ROI, pitch deliverables
│   ├── careeros-crm/                        # relationship timeline for every contact
│   ├── careeros-personal-brand/             # project -> case study -> social content -> resume
│   ├── careeros-offer-negotiation/          # offer -> Opportunity Value -> negotiation script
│   ├── careeros-client-success/             # post-contract lifecycle + computed client stage
│   ├── careeros-financial-intelligence/     # income, hourly rate, trends, strategy comparison
│   ├── careeros-opportunity-prediction/     # predicts demand from real company signals
│   ├── careeros-learning-lab/               # A/B experiments across generated content
│   ├── careeros-career-intelligence/        # combines signals into ranked recommendations
│   ├── careeros-ceo-agent/                  # evidence-weighted effort allocation across divisions
│   ├── careeros-workflow-builder/           # no-code WHEN/THEN rules over platform events
│   ├── careeros-dashboard/                  # the product UI (Streamlit)
│   ├── careeros-analytics/                  # funnel metrics + Career ROI breakdown
│   ├── careeros-trust-layer/                # audit log, consent, rate limiting, failure queue
│   ├── careeros-zero-cost-mode/             # provider cost registry + workspace dependency audit
│   ├── careeros-self-hosted/                # platform health check + local data dir bootstrap
│   ├── careeros-plugin-marketplace/         # Integrations catalog on top of Phase 3's registry
│   └── careeros-skill-marketplace/          # AI Skills catalog + unified marketplace search
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
