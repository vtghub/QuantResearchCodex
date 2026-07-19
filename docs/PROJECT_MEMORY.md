# Project Memory

## Current State

- Repository began empty on `main`.
- Git remote `origin` is `https://github.com/vtghub/QuantResearchCodex`.
- Implementation work is on `feature/ui-experiment-promotion`.
- The approved Terra plan is in `docs/IMPLEMENTATION_PLAN.md`.
- First scaffold milestone has been implemented and locally verified.
- The first web UI navigation feature slice is implemented and locally verified.
- API-backed console hydration is implemented and locally verified.
- Database model and Alembic migration foundation is implemented and locally verified.
- OpenAPI generated client and contract drift checks are implemented and locally verified.
- Job orchestration and adapter-backed ingestion jobs are implemented and locally verified.
- Vectorized research and backtest execution is implemented and locally verified.
- Auth/RBAC request-context enforcement is implemented and locally verified.
- Persistent local accounts and OIDC/OAuth hooks are implemented and locally verified.
- Paper-trading broker sandbox gates are implemented and locally verified.
- Risk policy approvals and tenant kill-switch state are implemented and locally verified.
- Durable job-state abstractions and local JSON persistence are implemented and locally verified.
- Dataset storage manifests and artifact versioning foundations are implemented and locally verified.
- Experiment comparison and strategy promotion UI surfaces are implemented and locally verified.

## Locked Decisions

- FastAPI backend and React + Vite SPA.
- Research, backtesting, paper trading, and controlled live trading.
- Multi-asset data and execution plug-ins; Alpaca and Interactive Brokers first broker interfaces.
- Free-first data, RBAC, local accounts plus OIDC/OAuth hooks, Docker/Helm, and Azure-first infrastructure.
- `feature/*` to `develop` to `main`, protected by CI and reviews.
- MCP-native-core is developer-only tooling pinned to `16888c0566e27cb10c589b73e68351136b7d1b5d`.
- Live trading interfaces can be scaffolded, but live execution must remain disabled until paper/sandbox gates exist.

## Architecture Map

- `apps/api` - FastAPI API, worker entrypoint, API schemas, and service wiring.
- `apps/web` - React + Vite + TypeScript operator UI.
- `packages/quant_core` - stable quant contracts, domain types, lifecycle states, and audit/risk abstractions.
- `packages/quant_adapters` - free-first market-data and broker adapter implementations or placeholders.
- `infra` - Docker Compose, Helm, and Azure-first Terraform.
- `.github/workflows` - CI gates for backend, frontend, infra, containers, and drift checks.

## Known Risks

- Free market-data vendors have licensing, rate-limit, redistribution, and continuity risks; every adapter must record provenance and entitlements.
- Live trading requires strict environment separation, encrypted secret references, two-person approval by default, reconciliation, idempotency, and kill switches.
- Multi-tenant isolation must be enforced at API, database, object-storage, and job levels before real users or trading data are onboarded.
- The first scaffold intentionally uses placeholder implementations for several adapters and workflows.

## Next Milestone

- Add observability, audit export, and deployment polish.

## Change Log

- 2026-07-18: Initialized project memory.
- 2026-07-18: Adopted Terra plan and started `feature/bootstrap-scaffold` implementation.
- 2026-07-18: Added first monorepo scaffold for FastAPI, React/Vite, quant contracts, adapters, Docker Compose, Helm, Terraform, GitHub Actions, and MCP-native-core developer docs.
- 2026-07-18: Verified backend with `pytest` and `ruff`; verified frontend with Vite build, Vitest unit test, and Playwright Chromium smoke test.
- 2026-07-18: Added pnpm v11 `allowBuilds` policy for `esbuild` in `pnpm-workspace.yaml`.
- 2026-07-18: Implemented web navigation console so sidebar and status cards switch real panels instead of acting as stubs.
- 2026-07-18: Implemented API-backed console feature with `/api/v1/console`, typed web client, static fallback mode, and browser/unit/API coverage.
- 2026-07-18: Implemented database foundation with tenant-aware SQLAlchemy models, Alembic async migration config, initial schema migration, metadata tests, and offline SQL migration validation.
- 2026-07-18: Implemented generated OpenAPI client, committed OpenAPI schema, wired the web console to generated types, and added CI drift plus Compose contract checks.
- 2026-07-18: Implemented job orchestration and ingestion phase with queue contracts, adapter-backed ingestion execution, job API endpoints, worker run-once hook, tests, and regenerated OpenAPI schema.
- 2026-07-18: Implemented vectorized research and backtest phase with deterministic moving-average signals, cost-aware portfolio metrics, job integration, and focused tests.
- 2026-07-18: Implemented auth/RBAC foundation with role-gated API dependencies, stable default tenant/workspace context, route-level permission tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented persistent local account hooks with hashed passwords, signed bearer tokens, seeded admin login, OIDC/OAuth provider discovery hooks, tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented paper-trading broker sandbox gates with trader/admin-only order submission, paper-only enforcement, notional caps, idempotency replay, Alpaca/IBKR adapter routing, tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented risk controls with tenant-scoped policy summaries, mutable kill-switch state, broker kill-switch enforcement, two-person approval requests/decisions, tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented durable job-state foundation with `JobStore` abstraction, in-memory and JSON-file stores, Redis/Postgres-compatible placeholders, job state API, worker backend reporting, tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented dataset and artifact catalog foundation with tenant-scoped storage manifests, checksum/provenance fields, strategy/backtest artifact versions, API routes, tests, and regenerated OpenAPI schema.
- 2026-07-19: Implemented web UI experiment comparison and strategy promotion surfaces with compact comparison metrics, promotion gates, responsive styling, and updated Vitest coverage.
