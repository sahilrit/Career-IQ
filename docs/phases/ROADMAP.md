# CareerOS Roadmap

**Final product:** a general-purpose, multi-tenant **AI Career Operating
System / AI Personal Career Agency SaaS**.

**Core principle:** build the platform once. Everything else — job boards,
freelance platforms, AI capabilities, workflows, agents, integrations — is
replaceable.

**Critical constraint:** no mandatory paid API keys. Development and the
core platform must be buildable using free/open-source/local software,
browser automation, public web data, user-provided credentials/OAuth where
appropriate, and pluggable providers.

This document is the single source of truth for phase sequencing. Update a
phase's status marker (⏳ planned / 🚧 in progress / ✅ done) as work lands;
do not fork this plan into other documents.

---

## PHASE 1 — Repository Foundation ✅

**Goal:** create the engineering foundation.

**Built:**
- Monorepo (uv workspace, `packages/*`)
- Python / `uv`
- Ruff (lint + format)
- Pytest
- pre-commit
- Package structure (`packages/careeros-common` as the first shared package)
- Configuration system (layered YAML + env vars, no required secrets)
- Documentation structure (`docs/architecture`, `docs/development`, `docs/phases`)
- Development standards

**Exit:** stable repository and quality gates. See
[phase-01-repository-foundation.md](phase-01-repository-foundation.md) for
what actually shipped.

## PHASE 2 — Career Brain Foundation ✅

**Goal:** create the source of truth for professional identity.

**Built:**
- Identity
- Experience
- Skills
- Achievements
- Projects
- Goals
- Preferences
- Companies
- Recruiters
- Applications
- Career entities
- Domain rules

**Principle:** AI does not invent the user's career. Career Brain is
authoritative.

## PHASE 3 — Plugin SDK ✅

**Goal:** create the foundation for the future plugin ecosystem.

**Built:**
- Plugin interface
- Plugin manifests
- Capabilities
- Versioning
- Registry
- Plugin validation
- Dependency handling
- Enable/disable lifecycle

**Future requirement:** a plugin must be independently installable and
removable.

## PHASE 4 — Event Bus ✅

**Goal:** stop agents/plugins from directly depending on each other.

```
Event
  ↓
Event Bus
  ↓
Subscribers
  ↓
Actions
```

**Principle:** plugins communicate through events rather than hard-coded
agent-to-agent calls.

## PHASE 5 — Memory Layer ✅

**Goal:** give CareerOS persistent memory.

**Memory types:**
- Career Brain
- Long-term memory
- Working memory
- Application history
- Company history
- Recruiter history
- Interview history
- Outcome history
- Analytics

**Architecture:** structured data remains authoritative. Vector/semantic
memory is derived from authoritative records.

## PHASE 6 — Job Provider Framework ✅

**Goal:** create a standardized way of connecting opportunity sources.

**Built:** provider SDK for:
- Job discovery
- Normalization
- Filtering
- Pagination
- Deduplication
- Location
- Salary
- Search
- Provider health

**Important abstraction:**

```
Capability: FIND_JOBS
  → LinkedIn
  → Indeed
  → RemoteOK
  → Wellfound
  → Naukri
  → ...
```

The rest of CareerOS doesn't care which provider supplied the job.

## PHASE 7 — RemoteOK Provider ✅

**Goal:** build the first real opportunity provider.

**Built:**
- HTTP client
- Parser
- Normalizer
- Deduplication
- Provider interface
- Tests

This became the reference implementation for job providers.

## PHASE 8 — End-to-End Job Discovery Pipeline ✅

**Goal:**

```
Discover → Normalize → Deduplicate → Score → Store → Emit Event
```

**Result:** CareerOS can process real job opportunities through the
platform architecture.

## PHASE 9 — Runtime Infrastructure ✅

**Goal:** turn individual functions into a continuously running system.

**Built:**
- Runtime
- Workers
- Queue
- Scheduler
- Lifecycle
- Registry
- Health
- Event handling
- Worker pools

This is the foundation for 24/7 operation.

## PHASE 10 — Autonomous Job Agent ✅

**Goal:** create intelligent opportunity discovery.

```
Career Brain → Job Discovery → Matching → Scoring → Prioritization → Action
```

**Principle:** the system doesn't simply find jobs. It determines: "Is this
opportunity worth pursuing?"

## PHASE 11 — Career Brain Engine ✅

**Goal:** make Career Brain intelligent instead of merely being storage.

**Built:**
- Profile matching
- Resume intelligence
- Recommendations
- Experience analysis
- Achievement matching
- Skill matching
- Career rules
- Memory integration

This became the foundation for personalized AI decisions.

## PHASE 12 — Application Engine ✅

**Goal:** generate application materials from Career Brain.

**Built:**
- Resume generation
- Cover letters
- Application answers
- Templates
- ATS-related logic
- Exports
- Application packages

**Principle:** every application can be personalized.

```
Job → Career Brain → Match → Resume → Cover Letter → Answers
```

## PHASE 13 — Browser Automation Engine ✅

**Goal:** give CareerOS the ability to interact with websites.

**Built:**
- Browser abstraction
- Sessions
- Navigation
- Cookies
- Forms
- Uploads
- Downloads
- Screenshots
- Waiting
- Selectors
- Browser health

**Important:** this provides the infrastructure for platforms that don't
expose useful free APIs.

## PHASE 14 — Application Runner ✅

**Goal:** turn application packages into actual browser submissions.

**Built:**
- Form handler
- Validator
- Upload system
- Screenshot system
- Retry system
- Pipeline
- Runner
- Health checks

## PHASE 15 — Application Workflow / CLI Integration ✅

**Goal:** expose application capabilities through CareerOS runtime and CLI.

**Built:**
- CLI integration
- Application workflow integration
- Runtime integration
- Search/application command infrastructure

## PHASE 16 — Production Application Intelligence ✅

**Goal:** make applications intelligent rather than blindly automated.

**Built:**
- Application intelligence
- Better matching
- Application decisions
- Application state
- Production-oriented safeguards
- Outcome tracking

## PHASE 17 — Live Browser + Human-in-the-Loop Execution ✅

**Goal:** support real browser execution while retaining human takeover.

```
AI executes → Problem detected → Human takeover → Human resolves → AI resumes
```

This is extremely important for real-world websites.

## PHASE 18 — Freelancer Provider ✅

**Goal:** expand CareerOS beyond employment.

**Built:** freelance opportunity provider architecture.

## PHASE 19 — Fiverr Provider ✅

**Goal:** prove the provider architecture works across freelance
marketplaces.

**Built:**
- Fiverr provider
- Parser
- HTTP layer
- Normalization
- Deduplication
- Provider tests

## PHASE 20 — Freelance & Opportunity Intelligence ✅

**Goal:** create the second major opportunity engine.

Instead of "find jobs", CareerOS now thinks "find opportunities". Covers:
- Employment
- Freelance
- Clients
- Consulting
- Opportunities
- Opportunity scoring
- Client intelligence
- Proposal generation
- CRM concepts

## PHASE 21 — Autonomous Decision & Authorization System ✅

**Goal:** allow CareerOS to operate autonomously.

**Built:**
- `FULL_AUTONOMOUS` mode
- Authorization engine
- Decision memory
- Risk-based authorization
- Rate limits
- Autonomy controls
- Policy engine
- Strategy
- Learning

**Critical requirement:** the system should not require approval for every
qualified application. In `FULL_AUTONOMOUS` mode:

```
Find qualified opportunity → Evaluate → Authorize → Apply
```

No arbitrary daily application cap — it continues while qualified
opportunities remain.

**Hard boundaries:** CareerOS must not fabricate experience, qualifications,
achievements, credentials, or employment history. Autonomy must not
silently perform high-risk actions such as financial/legal commitments or
changing core identity credentials.

## PHASE 22 — Autonomous Application Execution ✅

**Goal:** connect the autonomous decision system to the real browser
application engine.

**Architecture:**

```
Career Brain → Opportunity Engine → Scoring → Research → Application Builder
  → Autonomy Policy → Application Execution → Browser → Verification
  → CRM / Memory → Learning
```

---

## PHASE 23 — Platform Core Consolidation ✅

**Goal:** stop adding random features. Turn everything built so far into a
coherent platform.

**Build:**
- Core platform kernel
- Capability registry
- Unified service contracts
- Plugin lifecycle
- Configuration hierarchy
- Event contracts
- Shared execution context
- Shared identity/context
- Capability discovery
- Platform health
- Dependency boundaries

**Target:**

```
CareerOS Core
├── Career Brain
├── Memory
├── Event Bus
├── Runtime
├── Plugin SDK
├── Capability Registry
├── Workflow Engine
├── Authorization
└── Execution Engine
```

This becomes the immutable foundation.

## PHASE 24 — Capability Marketplace Architecture ✅

**Goal:** move from "which plugin should I call?" to "which capability do I
need?"

Example: `FIND_JOBS` → LinkedIn, RemoteOK, Indeed, Wellfound, Naukri, ...
Another: `FIND_CLIENTS` → Upwork, Fiverr, Freelancer, LinkedIn, Direct Web
Research, ...

**Build:**
- Capability contracts
- Provider ranking
- Capability discovery
- Provider fallback
- Parallel execution
- Result aggregation
- Provider health
- Capability versioning

## PHASE 25 — SaaS Identity & Multi-Tenancy ✅

This is where CareerOS becomes sellable.

**Build:** User → Organization → Workspace → Tenant → Roles → Permissions.

Each customer gets isolated: Career Brain, Memory, Applications,
Credentials, Plugins, Settings, Analytics.

**Security requirement:** customer A must never access customer B's data.

## PHASE 26 — Credential & Secret Management ✅

**Goal:** allow users to connect services without exposing credentials to
agents.

**Build:**
- OAuth abstraction
- Credential vault interface
- Encrypted secrets
- Per-plugin permissions
- Token lifecycle
- Credential rotation
- Audit logs
- Secret isolation

**Principle:** agent ≠ credential owner. Agents request capabilities; the
platform authorizes access.

## PHASE 27 — Gmail / Communication Intelligence ✅

**Goal:** turn incoming communication into structured career events.

Detect: interview, rejection, offer, recruiter message, follow-up, client
inquiry, contract, payment.

```
Email → Classification → Event → Workflow
```

## PHASE 28 — Calendar & Executive Assistant ✅

**Goal:** build the personal operations layer.

**Automatic interview workflow:**

```
Interview Email → Extract date → Extract time → Detect timezone
  → Detect platform → Extract meeting link → Identify interviewers
  → Identify interview stage → Create Calendar Event
```

**Event workspace contains:** job description, resume, cover letter,
company research, interviewer information, outreach thread, interview
notes.

## PHASE 29 — Interview Intelligence Division

**48 hours before — automatically prepare:** company research, business
model, products, competitors, recent developments, marketing, Meta Ads
where available, website/CRO analysis, interviewer background.

**24 hours before — generate:** likely questions, STAR answers,
role-specific questions, technical questions, company-specific questions.

**2 hours before — generate:** one-page briefing, strongest achievements,
questions to ask, compensation strategy, things to avoid.

## PHASE 30 — Employment Division 2.0

**Goal:** complete the employment agency.

```
Discovery → Scoring → Research → Resume → Portfolio → Cover Letter
  → Recruiter → Outreach → Application → Follow-up → Interview
  → Offer → Negotiation
```

Add support for additional providers through plugins.

## PHASE 31 — Freelance Client Acquisition Division

This becomes a major differentiator.

```
Company Discovery → Company Qualification → Problem Detection
  → Opportunity Score → Audit → Personalized Outreach → Follow-up
  → Proposal → Call → Contract → Client
```

**Research signals:** Shopify, Meta Ads, website, CRO, product pages,
creatives, competitors, technology, hiring, growth signals.

## PHASE 32 — AI Audit & Proposal Engine

**Automatically generate:**

**Shopify audit:** UX, CRO, product page, checkout, offer, pricing, trust,
mobile experience.

**Meta Ads audit:** creative, messaging, funnel, retargeting, landing page,
offer, competitive positioning.

**Output:** audit + Loom script + PDF + email + LinkedIn message + proposal
+ ROI estimate.

## PHASE 33 — CRM & Relationship Intelligence

CareerOS becomes a real relationship-management system.

**Track:** recruiters, founders, CMOs, hiring managers, agency owners,
clients, prospects.

**Relationship timeline:**

```
Viewed → Liked → Commented → Connected → Messaged → Conversation
  → Opportunity → Client / Employer
```

## PHASE 34 — Personal Brand Division

Turn career activity into public assets. One achievement can become:

```
Project → Case Study → Portfolio → LinkedIn Post → X Thread → Blog
  → Resume Achievement
```

**Build:** content engine, case-study generator, portfolio generator,
personal website, LinkedIn content, GitHub project presentation,
testimonials, social proof.

## PHASE 35 — Offer Evaluation & Negotiation Intelligence

**Analyze:** salary, bonus, equity, benefits, equipment, leave, remote
policy, timezone, stability, growth, reputation, tax implications, payment
reliability, effective compensation.

**Then calculate:** Opportunity Value — not merely salary.

## PHASE 36 — Client Success Division

After landing freelance work, manage: contracts, deliverables, meetings,
notes, reports, invoices, payments, upsells, renewals, testimonials,
referrals.

**Goal:** One Client → Repeat Client → Long-term Client → Referral.

## PHASE 37 — Financial Intelligence

**Track:** salary, freelance revenue, client revenue, invoices, outstanding
payments, hourly rate, effective hourly rate, taxes, income trends.

**Compare:** full-time opportunity vs. freelance opportunity vs. combined
strategy.

## PHASE 38 — Opportunity Prediction Engine

Stop reacting to opportunities. Start predicting them.

**Signals:** funding, hiring velocity, new products, expansion, executive
hires, marketing team growth, agency expansion, new markets, technology
changes.

```
Company shows strong hiring signals → CareerOS predicts likely demand
  → Research company → Identify decision maker → Begin relationship
  → Opportunity appears → Already positioned
```

## PHASE 39 — AI Learning Lab

CareerOS begins optimizing itself.

**Experiment with:** resume A/B, email A/B, LinkedIn A/B, portfolio A/B,
proposal A/B, subject line A/B.

**Measure:** response rate, interview rate, offer rate, client conversion,
revenue. Then automatically learn what works best.

## PHASE 40 — Career Intelligence Engine

Combine every signal. The system should eventually answer: which roles,
companies, industries, clients, countries, salary range, skills, platform,
outreach strategy, resume, career direction should I pursue?

This is where CareerOS becomes genuinely intelligent rather than merely
automated.

## PHASE 41 — Executive AI / CEO Agent

The CEO Agent becomes the strategic coordinator. It receives Career Brain +
Memory + Market Intelligence + Opportunity Data + Financial Data +
Analytics, and decides where resources should go, e.g.:

```
Employment       40%
Freelance        35%
Networking       15%
Personal Brand   10%
```

These percentages change based on results.

## PHASE 42 — Unified Automation & Workflow Builder

Users should be able to create rules without coding, e.g.:

```
WHEN job.score > 90
THEN research_company → build_resume → create_cover_letter
  → find_recruiter → apply → send_outreach → update_crm
```

```
WHEN interview.confirmed
THEN calendar_event → company_research → interviewer_research
  → mock_interview → briefing
```

```
WHEN new_shopify_opportunity.score > 85
THEN generate_audit → generate_outreach → create_followup_sequence
  → add_to_crm
```

## PHASE 43 — Dashboard / SaaS Control Center

Build the actual product UI.

**Main dashboard:** today's opportunities, applications, interviews,
offers, freelance leads, clients, revenue, network, tasks, notifications.

**Opportunity page:** score, company, job, research, resume, application,
recruiter, outreach, status, timeline.

**Career Brain UI:** manage experience, skills, projects, achievements,
preferences, portfolio, goals.

## PHASE 44 — Analytics & Career ROI

Track the entire system: jobs found, applications, response rate,
interview rate, offer rate, acceptance rate, freelance leads, proposals,
calls, clients, revenue, cold emails, LinkedIn outreach, network growth,
resume performance, proposal performance, platform performance, industry
performance.

**Career ROI** = salary + freelance revenue + equity + network + personal
brand + skills + future opportunity value.

## PHASE 45 — Security & Trust Layer

Enterprise-grade security.

**Build:** tenant isolation, encryption, OAuth, secret management,
permission boundaries, audit logs, action history, data export, data
deletion, consent management, agent authorization, rate limiting,
recovery, failure queues.

Every autonomous action should be explainable: WHO, WHAT, WHY, WHEN, WHICH
POLICY, WHICH DATA, RESULT.

## PHASE 46 — Zero-Cost Infrastructure Mode

This phase is extremely important because of the original requirement:
CareerOS must not depend on paid APIs.

```
CareerOS
  ├── Local AI
  ├── Open-source models
  ├── Free providers
  ├── Browser automation
  ├── Public web research
  ├── User OAuth
  ├── Local databases
  └── Pluggable providers
```

Paid APIs are optional plugins — not core dependencies. The platform must
still function if every paid AI/API provider is disabled.

## PHASE 47 — Local / Self-Hosted Edition

Make CareerOS runnable on Mac, Windows, Linux, Docker, local server.

```
Local stack: CareerOS + PostgreSQL + Redis + Qdrant + Browser Engine
  + Local AI + Workers + Dashboard
```

This gives developers and users a way to operate the platform without
mandatory cloud services.

## PHASE 48 — Plugin Marketplace

Make the plugin ecosystem real: LinkedIn, Indeed, Naukri, RemoteOK, Upwork,
Fiverr, Gmail, Google Calendar, GitHub, Crunchbase, Apollo, Meta Ads,
Shopify — but the platform doesn't hard-code them.

Each plugin declares: ID, name, version, capabilities, permissions,
triggers, actions, tools, workflows, settings, dependencies, health.

## PHASE 49 — AI Skill Marketplace

Plugins can now contribute intelligence: resume optimization, company
intelligence, Meta Ads audit, Shopify CRO audit, interview preparation,
salary analysis, proposal optimization, LinkedIn optimization, career
strategy.

This creates two marketplace categories: INTEGRATIONS + AI SKILLS.

## PHASE 50 — Developer SDK

Release the official CareerOS SDK. A developer should be able to build a
`MyCareerPlugin` class and expose capabilities, actions, triggers, tools,
workflows, settings, and permissions — without modifying CareerOS Core.

## PHASE 51 — Marketplace Governance

Before third-party plugins can be distributed: manifest validation,
version validation, permission review, dependency validation, security
scanning, capability declarations, compatibility testing, plugin health,
version rollback.

This prevents the ecosystem from becoming dangerous or unstable.

## PHASE 52 — SaaS Billing & Plans

Only after the core product works.

**Possible product model:**
- **Free** — Career Brain, basic opportunity discovery, basic
  applications, limited automation.
- **Pro** — autonomous workflows, advanced research, freelance
  acquisition, interview intelligence, analytics.
- **Agency / Business** — multiple workspaces, team members, advanced
  automation, custom plugins, API, enterprise controls.

**Important:** billing is a SaaS monetization layer, not a dependency of
the core platform.

## PHASE 53 — Multi-User Production SaaS

Turn the platform into a real service:

```
Signup → Onboarding → Career Brain setup → Connect accounts
  → Choose capabilities → Configure autonomy → Start CareerOS
```

Each user gets their own AI career agency.

## PHASE 54 — Observability & Reliability

Enterprise-grade operations: metrics, logs, traces, health, queues,
retries, dead-letter queues, alerts, worker monitoring, plugin monitoring,
provider monitoring. The system must be able to explain failures.

## PHASE 55 — Security / Compliance / Data Portability

Prepare for real customers: privacy controls, data export, account
deletion, tenant isolation, audit trails, consent, data retention,
encryption, security policies, compliance architecture.

## PHASE 56 — Beta Release

Release the first real SaaS MVP: Career Brain + Opportunity Discovery +
Job Applications + Freelance Opportunities + Autonomous Execution + CRM +
Interview Preparation + Calendar + Dashboard. Start with a limited number
of users.

## PHASE 57 — Production Launch

Launch CareerOS publicly. The platform should now be: multi-tenant,
plugin-based, event-driven, autonomous, memory-driven, AI-powered,
browser-capable, SaaS-ready, zero-paid-API dependent.

## PHASE 58 — Ecosystem Expansion

After launch: more job providers, more freelance providers, more research
plugins, more AI skills, more workflows, more integrations, more
marketplace developers. The platform grows without changing the core.

## PHASE 59 — CareerOS Intelligence Network

Long-term vision: aggregate anonymous, consented, non-personal performance
signals across the platform to improve general strategies — which resume
structures work, which outreach patterns work, which skills are growing,
which industries are hiring, which freelance niches are growing.

Never expose one customer's private Career Brain to another.

## PHASE 60 — Autonomous Career Agency

This is the final destination. A user gives CareerOS: career goals,
preferences, experience, skills, compensation expectations, risk
tolerance, availability. CareerOS operates continuously:

```
                CAREEROS
                    │
       ┌────────────┼────────────┐
       ↓             ↓            ↓
 Employment      Freelance    Personal Brand
       │             │            │
       └─────────────┼────────────┘
                     ↓
                Networking
                     ↓
               Client Success
                     ↓
           Financial Intelligence
                     ↓
            Career Intelligence
                     ↓
                 CEO Agent
                     ↓
                 Learning
                     ↓
            Better Decisions
                     ↓
          Higher Lifetime Value
```

---

## Final Architecture

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

## Development Sequence

```
PHASE 1–5     Foundation
PHASE 6–10    Opportunity Discovery
PHASE 11–17   Career Intelligence + Application Execution
PHASE 18–20   Freelance Intelligence
PHASE 21–22   True Autonomous Execution
PHASE 23–26   Platform + SaaS Foundation
PHASE 27–35   Executive + Employment + Freelance Agency
PHASE 36–44   Client / Financial / Brand / Intelligence
PHASE 45–51   Security + Zero-Cost + Plugin Ecosystem
PHASE 52–57   SaaS + Beta + Production
PHASE 58–60   Ecosystem + Autonomous Career Agency
```
