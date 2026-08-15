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

## Current state (post Phase 1)

```
careeros/                      workspace root — virtual, not installed
└── packages/
    └── careeros-common/       shared kernel utilities
        ├── config.py          layered YAML + env settings
        ├── logging.py         stdlib logging setup
        └── exceptions.py      CareerOSError base hierarchy
```

Nothing else exists yet: no Career Brain, no event bus, no plugin runtime,
no providers, no browser automation, no persistence layer. Every package
added from Phase 2 onward depends on `careeros-common` for config,
logging, and its base exception type — it does not duplicate them.

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
