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

## Current state (post Phase 10)

```
careeros/                          workspace root — virtual, not installed
└── packages/
    ├── careeros-common/           shared kernel: config, logging, exceptions,
    │                              generic SQLite DocumentStore
    ├── careeros-career-brain/     authoritative domain models (Identity,
    │                              Experience, Skills, Applications, ...) +
    │                              CareerBrainRepository
    ├── careeros-plugin-sdk/       Plugin interface, manifest, versioning,
    │                              PluginRegistry lifecycle
    ├── careeros-event-bus/        in-process pub/sub EventBus
    ├── careeros-memory/           working memory, HistoryLog (subscribes to
    │                              the event bus), analytics, local TF-IDF
    │                              semantic search
    ├── careeros-job-providers/    FIND_JOBS provider SDK: JobPosting model,
    │                              filtering, dedup, JobProviderRegistry
    ├── careeros-remoteok-provider/ the reference FIND_JOBS provider, backed
    │                              by RemoteOK's free public API
    ├── careeros-job-discovery/    end-to-end pipeline: discover -> score
    │                              -> store -> emit events
    ├── careeros-runtime/          WorkerPool, Scheduler, Runtime lifecycle
    │                              for continuous background operation
    └── careeros-job-agent/        JobAgent: discovery + qualification
                                   policy, wired onto Runtime as a
                                   recurring job
```

Every package depends on `careeros-common` for config, logging, and its
base exception type rather than duplicating them. Career Brain
(`careeros-career-brain`) is the only authoritative store of a user's
professional identity — every other package reads or appends to it, none
invents data about the user.

Still missing: multi-tenancy (Phase 25), a resume/application-material
generator (Phase 12), browser automation (Phase 13), freelance providers
(Phase 18+), and everything from Platform Core Consolidation (Phase 23)
onward. See [`docs/phases/ROADMAP.md`](../phases/ROADMAP.md) for the full
sequence and current status markers.

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
