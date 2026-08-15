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

🚧 Phase 1 of 60 — Repository Foundation. See
[`docs/phases/ROADMAP.md`](docs/phases/ROADMAP.md) for the full plan and
[`docs/phases/phase-01-repository-foundation.md`](docs/phases/phase-01-repository-foundation.md)
for what's shipped so far.

## Repository layout

```
careeros/
├── packages/               # uv workspace members
│   └── careeros-common/    # shared config, logging, base exceptions
├── config/                 # layered YAML configuration (default/dev/test/prod/local)
├── docs/
│   ├── architecture/       # current-state architecture docs
│   ├── development/        # setup + coding standards
│   └── phases/             # the roadmap and per-phase notes
└── pyproject.toml          # workspace root (virtual — not itself installed)
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
