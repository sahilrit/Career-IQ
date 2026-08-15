# Architecture Overview

CareerOS is a general-purpose, multi-tenant AI Career Operating System.
The full target architecture (post Phase 60) looks like this:

```
                         CAREEROS
                   AI CAREER PLATFORM
                            │
                     ┌──────▼──────┐
                     │  CEO AGENT  │
                     └──────┬──────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         EMPLOYMENT      FREELANCE     PERSONAL BRAND
              │             │             │
              └─────────────┼─────────────┘
                            │
                      OPPORTUNITY
                       INTELLIGENCE
                            │
             ┌──────────────┼──────────────┐
             │              │              │
        CAREER BRAIN      MEMORY       ANALYTICS
             │              │              │
             └──────────────┼──────────────┘
                            │
                       EVENT BUS
                            │
                     WORKFLOW ENGINE
                            │
                   CAPABILITY REGISTRY
                            │
                    PLUGIN MANAGER
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
   JOB PLUGINS         FREELANCE PLUGINS    AI SKILLS
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    EXECUTION ENGINE
                            │
                    BROWSER AUTOMATION
                            │
                    LOCAL / FREE AI
                            │
                    SaaS INFRASTRUCTURE
```

See [`docs/phases/ROADMAP.md`](../phases/ROADMAP.md) for how the platform
gets there phase by phase. This document describes only what exists
**today**; update it as each phase lands instead of describing the target
state as if it were current.

## Current state (post Phase 52)

```
careeros/                                  workspace root — virtual, not installed
└── packages/
    ├── careeros-common/                    shared kernel: config, logging, exceptions,
    │                                       generic SQLite DocumentStore
    ├── careeros-career-brain/               authoritative domain models (Identity,
    │                                       Experience, Skills, Applications, ...) +
    │                                       CareerBrainRepository + status state machine
    ├── careeros-plugin-sdk/                 Plugin interface, manifest, versioning,
    │                                       PluginRegistry lifecycle
    ├── careeros-event-bus/                  in-process pub/sub EventBus
    ├── careeros-memory/                     working memory, HistoryLog (subscribes to
    │                                       the event bus), analytics, local TF-IDF
    │                                       semantic search
    ├── careeros-job-providers/              FIND_JOBS provider SDK: JobPosting model,
    │                                       filtering, dedup, JobProviderRegistry
    ├── careeros-remoteok-provider/          the reference FIND_JOBS provider, backed
    │                                       by RemoteOK's free public API
    ├── careeros-job-discovery/              end-to-end pipeline: discover -> score
    │                                       -> store -> emit events
    ├── careeros-runtime/                    WorkerPool, Scheduler, Runtime lifecycle
    │                                       for continuous background operation
    ├── careeros-job-agent/                  JobAgent: discovery + qualification
    │                                       policy, wired onto Runtime as a
    │                                       recurring job
    ├── careeros-career-brain-engine/        profile matching, skill/achievement
    │                                       ranking, experience analysis,
    │                                       rule-based recommendations
    ├── careeros-application-engine/         resume/cover-letter/answers/ATS
    │                                       generation from Career Brain — nothing
    │                                       fabricated, no paid AI required
    ├── careeros-browser/                    BrowserSession abstraction
    │                                       (Playwright-backed), including
    │                                       multi-element query_all() for
    │                                       scraping-style providers, +
    │                                       FakeBrowserSession test double
    │                                       used across the platform
    ├── careeros-application-runner/         turns an application package into a
    │                                       real browser form submission, with
    │                                       validation/retries/screenshots
    ├── careeros-cli/                        the `careeros` command-line interface
    ├── careeros-application-intelligence/   production apply decisions (score +
    │                                       rate limits + cooldowns) and outcome
    │                                       tracking
    ├── careeros-human-in-the-loop/          problem detection + AI/human handoff
    │                                       state machine for live browser runs
    ├── careeros-freelance-providers/        FIND_GIGS provider SDK, mirroring
    │                                       job-providers for freelance marketplaces
    ├── careeros-fiverr-provider/            a second FIND_GIGS provider (browser-
    │                                       driven), proving the architecture
    │                                       generalizes
    ├── careeros-opportunity-intelligence/   unifies employment + freelance under
    │                                       one Opportunity abstraction, unified
    │                                       scoring, a lightweight Client CRM,
    │                                       and freelance proposal generation
    ├── careeros-autonomy/                   risk-based authorization
    │                                       (MANUAL/SUPERVISED/FULL_AUTONOMOUS),
    │                                       decision memory, pacing, hard
    │                                       high-risk boundaries, strategy presets
    ├── careeros-autonomous-execution/       the capstone loop: qualified
    │                                       application -> authorize -> build
    │                                       package -> submit via real browser
    │                                       -> verify -> record outcome, with
    │                                       human handoff on any failure
    ├── careeros-core/                       platform-wide contracts: capability
    │                                       registry interface, platform health,
    │                                       execution context, event contracts
    ├── careeros-capability-marketplace/     ranked provider registration with
    │                                       automatic fallback and parallel
    │                                       execution across any capability
    ├── careeros-tenancy/                    multi-tenant identity (User /
    │                                       Organization / Workspace /
    │                                       Membership / Role), and
    │                                       TenantScopedDocumentStore — gives
    │                                       tenant isolation to any existing
    │                                       DocumentStore-based repository
    │                                       with zero changes to that repo
    ├── careeros-credentials/                encrypted credential vault
    │                                       (Fernet), permissioned access,
    │                                       audit log, OAuth token lifecycle
    ├── careeros-communication-intelligence/ classifies inbound email
    │                                       (interview / offer / rejection /
    │                                       other) and publishes
    │                                       communication.*_detected events
    ├── careeros-calendar-assistant/         extracts interview details from
    │                                       email, builds calendar events,
    │                                       tracks an EventWorkspace per
    │                                       interview
    ├── careeros-interview-intelligence/     company research (no
    │                                       fabrication), STAR question
    │                                       generation, briefing documents on
    │                                       a H48/H24/H2 schedule
    ├── careeros-employment-division/        completes the employment agency
    │                                       pipeline end-to-end (Discovery ->
    │                                       ... -> Negotiation), tracking
    │                                       per-application progress purely
    │                                       via event-type strings — zero new
    │                                       dependencies on the packages whose
    │                                       events it observes
    ├── careeros-client-acquisition/         the freelance-side mirror of
    │                                       Employment Division: Company
    │                                       Discovery -> Qualification ->
    │                                       Problem Detection -> Score ->
    │                                       Audit -> Outreach -> Follow-up
    │                                       -> Proposal -> Call -> Contract
    │                                       -> Client, with website
    │                                       problem-signal detection via
    │                                       careeros-browser
    ├── careeros-audit-proposal-engine/      deep Shopify/Meta Ads audits,
    │                                       heuristic ROI estimation, and
    │                                       every pitch deliverable (Loom
    │                                       script, real PDF via fpdf2,
    │                                       email, LinkedIn message,
    │                                       proposal) plugging into Client
    │                                       Acquisition's AUDIT stage
    ├── careeros-crm/                        relationship timeline (Viewed
    │                                       -> ... -> Client/Employer) for
    │                                       every contact across both
    │                                       employment and freelance sides,
    │                                       wired to company.qualified /
    │                                       client.won / outcome.recorded
    ├── careeros-personal-brand/             turns a Project into a Case
    │                                       Study, then a portfolio page,
    │                                       LinkedIn post, X thread, blog
    │                                       post, and candidate resume
    │                                       achievement, plus a
    │                                       user-supplied testimonials store
    ├── careeros-offer-negotiation/          analyzes an offer beyond
    │                                       salary (bonus/equity/
    │                                       benefits/PTO/stability/
    │                                       growth/reputation) into one
    │                                       comparable Opportunity Value,
    │                                       plus negotiation talking
    │                                       points and a call script
    ├── careeros-client-success/             post-contract lifecycle:
    │                                       contracts, deliverables,
    │                                       invoices, referrals, and a
    │                                       computed (never manually
    │                                       assigned) lifecycle stage
    ├── careeros-financial-intelligence/     real income tracking,
    │                                       effective hourly rate,
    │                                       income trends, and full-time
    │                                       vs. freelance vs. combined
    │                                       strategy comparison
    ├── careeros-opportunity-prediction/     predicts demand from real
    │                                       company signals (funding,
    │                                       hiring velocity computed
    │                                       from real job posting dates,
    │                                       executive hires, ...) before
    │                                       an opportunity is posted
    ├── careeros-learning-lab/               A/B experiments across
    │                                       content generated elsewhere
    │                                       (resume, email, LinkedIn,
    │                                       portfolio, proposal, subject
    │                                       line), tracking real
    │                                       outcomes to find a winner
    ├── careeros-career-intelligence/        combines signals already
    │                                       computed elsewhere into
    │                                       ranked recommendations
    │                                       (roles, companies, skills,
    │                                       ...) and a career direction
    │                                       summary — a pure combinator,
    │                                       not a new data source
    ├── careeros-ceo-agent/                  allocates effort across
    │                                       Employment/Freelance/
    │                                       Networking/Personal Brand as
    │                                       a transparent, evidence-
    │                                       weighted blend of a baseline
    │                                       split and real performance
    ├── careeros-workflow-builder/            no-code WHEN/THEN rules
    │                                       over platform events,
    │                                       dispatching named action
    │                                       chains through a pluggable
    │                                       executor
    ├── careeros-dashboard/                  the product UI (Streamlit):
    │                                       main dashboard, opportunity
    │                                       page, full Career Brain
    │                                       manager — reads the same
    │                                       local database the CLI
    │                                       writes to
    ├── careeros-analytics/                  funnel/platform/industry/
    │                                       network metrics and a
    │                                       transparent Career ROI
    │                                       breakdown, computed live
    │                                       from real platform data
    ├── careeros-trust-layer/                general-purpose audit log,
    │                                       consent records, rate
    │                                       limiting, a failure queue
    │                                       with recovery, and an
    │                                       extensible data export/
    │                                       deletion registry
    ├── careeros-zero-cost-mode/              makes "no mandatory paid
    │                                       API" explicit and tested: a
    │                                       provider cost registry
    │                                       (pre-seeded with the
    │                                       platform's own real
    │                                       providers) and a workspace
    │                                       dependency audit
    ├── careeros-self-hosted/                real platform health
    │                                       checks and a canonical
    │                                       local data directory — the
    │                                       code half of "runnable on
    │                                       Mac/Windows/Linux/Docker"
    ├── careeros-plugin-marketplace/         a browsable catalog on top
    │                                       of Phase 3's PluginRegistry
    │                                       — RemoteOK/Fiverr
    │                                       installable, everything
    │                                       else honestly catalog-only
    ├── careeros-skill-marketplace/           the second marketplace
    │                                       section (AI Skills):
    │                                       intelligence CareerOS's own
    │                                       packages already provide,
    │                                       plus a unified search over
    │                                       both marketplace sections
    ├── careeros-developer-sdk/              a fluent PluginBuilder,
    │                                       manifest validation, and a
    │                                       package scaffold generator
    │                                       — build a plugin without
    │                                       touching CareerOS Core
    ├── careeros-marketplace-governance/     the checks a plugin must
    │                                       pass before distribution
    │                                       (manifest/version/
    │                                       permission/dependency/
    │                                       security/compatibility),
    │                                       plus version rollback
    └── careeros-billing/                    the Free/Pro/Agency plan
                                            model, feature gating, and
                                            subscription state tracking
                                            — a monetization layer, not
                                            a core dependency; no real
                                            payment processor integrated
```

Every package depends on `careeros-common` for config, logging, and its
base exception type rather than duplicating them. Career Brain
(`careeros-career-brain`) is the only authoritative store of a user's
professional identity — every other package reads or appends to it, none
invents data about the user.

Still missing: multi-user production hardening (Phase 53), observability
(Phase 54), the compliance pass (Phase 55), and the beta/launch
milestones (Phase 56-60). See
[`docs/phases/ROADMAP.md`](../phases/ROADMAP.md) for the full sequence
and current status markers.

## Core principle

Build the platform once. Job boards, freelance platforms, AI capabilities,
workflows, agents, and integrations are all replaceable — implemented as
plugins/providers behind stable capability contracts (from Phase 24
onward), never hard-coded into the core.

## Critical constraint

No mandatory paid API keys. Every core capability must have a free/local
path: open-source or local models, free-tier or public-data providers,
browser automation, and user-supplied OAuth/credentials. Paid providers are
optional plugins layered on top, never a dependency of the core platform
(Phase 46, "Zero-Cost Infrastructure Mode", makes this an explicit,
tested requirement).
