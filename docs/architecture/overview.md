# Architecture Overview

CareerOS is a multi-tenant AI career operating system covering employment and
freelance work in one product.

This document describes what **exists today**. Where an earlier version of it
described a target architecture (a capability marketplace, a plugin manager, a
CEO agent orchestrating divisions), that layer has been removed: it was never
wired to anything, and seventeen packages implementing it were deleted in the
2026-08-31 rebuild. Documentation that describes intent as if it were
implementation is worse than none.

## The workflow that matters

Everything below exists to serve one path:

```
discover  →  score  →  generate  →  review  →  open the form
                                                    │
                                    detect → map → fill → verify
                                                    │
                                   submission-ready (a human submits)
```

`scripts/e2e_smoke.py` runs exactly this against live boards and real forms and
reports where it stops. That report, not the test suite, is the definition of
whether CareerOS works.

## Subsystem documentation

| Area | Document |
|---|---|
| Provider-agnostic AI, routing, fallback, health | [llm-providers.md](../llm-providers.md) |
| Aggregators and the nine hosted ATSes | [job-providers.md](../job-providers.md) |
| Package generation, filling, verification | [application-engine.md](../application-engine.md) |
| The source of truth, and the zero-fabrication rule | [career-profile.md](../career-profile.md) |
| How this is tested, at five levels | [testing.md](../testing.md) |
| When something does not work | [troubleshooting.md](../troubleshooting.md) |
| What was taken from ai-job-search, career-ops and AIHawk | [competitive-integration-log.md](../competitive-integration-log.md) |

## Principles

1. **Working functionality over architectural completeness.** A simple thing
   that applies to real ATS forms beats an abstraction that theoretically
   supports a hundred.
2. **Never fabricate.** Not a fact about the user, not an AI response, not a
   test result. Where a truthful value is unavailable, the field is left for a
   human and said so.
3. **Never fail silently.** A swallowed exception is how filling became
   unreliable while every test passed.
4. **A human before Submit.** Reliability is worth more than the claim of full
   autonomy.

## Package map

```
careeros/                                  workspace root — virtual, not installed
└── packages/
    ├── careeros-common/                    shared kernel: config, logging, exceptions,
    │                                       generic SQLite DocumentStore
    ├── careeros-career-brain/               authoritative domain models (Identity,
    │                                       Experience, Skills, Applications, ...) +
    │                                       CareerBrainRepository + status state machine
    ├── careeros-event-bus/                  in-process pub/sub EventBus
    ├── careeros-memory/                     working memory, HistoryLog (subscribes to
    │                                       the event bus), analytics, local TF-IDF
    │                                       semantic search
    ├── careeros-job-providers/              FIND_JOBS provider SDK: JobPosting model,
    │                                       filtering, dedup, JobProviderRegistry
    ├── careeros-ats-providers/              hosted-ATS discovery: one engine, nine
    │                                       adapters (greenhouse, lever, ashby,
    │                                       smartrecruiters, workable, recruitee,
    │                                       personio, bamboohr, workday) over 120
    │                                       live-verified company boards. The only
    │                                       sources whose forms can be filled
    │                                       end to end — see docs/job-providers.md
    ├── careeros-llm/                        the LLM gateway: task routing, provider
    │                                       fallback, health, and CLI providers
    │                                       (claude/codex/gemini) so an existing
    │                                       subscription is a working provider and
    │                                       no API key is ever required —
    │                                       see docs/llm-providers.md
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
    │                                       real browser form submission. Every
    │                                       field is written then READ BACK, and
    │                                       the FillReport says what landed, what
    │                                       was left for a human, and what failed
    │                                       — see docs/application-engine.md
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
    ├── careeros-billing/                    the Free/Pro/Agency plan
    │                                       model, feature gating, and
    │                                       subscription state tracking
    │                                       — a monetization layer, not
    │                                       a core dependency; no real
    │                                       payment processor integrated
    ├── careeros-compliance/                 retention policies,
    │                                       configurable security
    │                                       policies, whole-account
    │                                       deletion spanning both
    │                                       domain data (Phase 45) and
    │                                       tenancy records (Phase 25),
    │                                       and a compliance readiness
    │                                       report
    ├── careeros-arbeitnow-provider/         a second FIND_JOBS
    │                                       provider, backed by
    │                                       Arbeitnow's free public
    │                                       job board API, proving the
    │                                       SDK generalizes beyond
    │                                       RemoteOK
