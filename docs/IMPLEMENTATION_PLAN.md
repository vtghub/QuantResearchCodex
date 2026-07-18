# Quant Research & Trading Platform Plan

## Summary

Build a modular, multi-tenant quant platform for research, backtesting, paper trading, and controlled live trading across equities/ETFs, crypto, FX, and futures. Use a FastAPI backend, React + Vite SPA, open-source infrastructure, free-first data adapters, and Azure-first deployment artifacts with AWS/GCP extension hooks.

Create and maintain these tracked files from the first implementation commit:

- `docs/IMPLEMENTATION_PLAN.md` - this approved plan, kept current when scope changes.
- `docs/PROJECT_MEMORY.md` - incremental decision log, architecture map, setup status, known risks, and next steps; never store credentials or sensitive trading data.

## Architecture and Interfaces

- Establish a monorepo with FastAPI API/worker services, React/Vite frontend, reusable Python quant packages, Docker Compose, Helm charts, Terraform, and GitHub Actions.
- Use PostgreSQL for tenancy, identity, metadata, trading/audit ledger, and configuration; Redis for job/event coordination; MinIO/S3-compatible object storage for immutable raw data, Parquet datasets, models, and run artifacts; DuckDB/Polars/PyArrow for high-performance research queries.
- Provide tenant-aware REST and WebSocket APIs under `/api/v1` for identity, workspaces, data catalog/ingestion, research runs, datasets, strategies, backtests, portfolios, deployments, orders, risk events, and immutable audit records. Publish OpenAPI and generate the TypeScript client used by the SPA.
- Support local accounts, OIDC/OAuth SSO, RBAC, organization/workspace isolation, and roles for platform admin, organization admin, researcher, trader, and read-only viewer.
- Define plug-in contracts for:
  - Market-data providers: discovery, ingestion, normalization, entitlement metadata, retry/rate-limit handling, and vendor provenance.
  - Strategy modules: parameters, feature requirements, signal generation, portfolio construction, and versioned artifacts.
  - Backtest engines and cost models.
  - Execution brokers: unified account, positions, market-data, order, fill, and cancel interfaces.
  - Risk policies and approval workflows.
- Ship free-first adapters for sources such as FRED, Stooq, Yahoo Finance-compatible retrieval, CoinGecko, ECB/central-bank FX data, and exchange/broker public endpoints where terms permit. Record vendor terms, timestamp, symbols, checksums, transforms, and entitlements; prohibit unlicensed redistribution. Make paid-provider adapters opt-in through the same contract.
- Normalize instruments, exchange calendars, currencies, corporate actions, symbol mappings, and time zones before research data reaches strategies.

## Research, Validation, and Trading

- Provide reproducible research jobs with versioned datasets, parameter manifests, random seeds, package versions, source commit, generated metrics, charts, and artifacts.
- Include a vectorized research path and event-driven portfolio/backtest path. Validate strategies with fees, spreads, slippage, liquidity constraints, borrow/funding costs where applicable, corporate actions, partial fills, walk-forward/out-of-sample analysis, and anti-look-ahead/survivorship-bias checks.
- Support strategy lifecycle states: draft -> research-validated -> paper-approved -> live-approved -> paused/retired. Include configurable approval modes: two-person approval by default, owner approval, or explicitly enabled automated promotion.
- Implement Alpaca and Interactive Brokers broker adapters for paper and live modes. Enforce environment separation, encrypted secret references, per-strategy and per-tenant notional/position/loss limits, kill switches, idempotent order submission, reconciliation, and append-only audit trails.
- Build the React SPA around dashboards for data health, experiment comparison, backtest tear sheets, strategy promotion, paper/live portfolio monitoring, orders/fills, risk events, user/workspace administration, and audit history.

## Developer Tooling, Deployment, and CI

- Integrate `vtghub/MCP-native-core` as developer-only AI tooling, pinned to verified commit `16888c0566e27cb10c589b73e68351136b7d1b5d` until a release tag is available. Build it with Rust and configure `fast_search`/`parse_structure` for efficient codebase inspection; retain `rg` and language-native parsing as fallbacks. Do not make it a production runtime dependency.
- Provide local Docker Compose for the API, worker, SPA, Postgres, Redis, MinIO, and observability stack. Supply Helm charts for portable Kubernetes deployment.
- Deliver Azure-first Terraform and GitHub OIDC deployment configuration, with provider-neutral module boundaries and extension points for AWS and GCP equivalents.
- Use GitHub flow as `feature/*` -> pull request to protected `develop` -> validated release pull request from `develop` to protected `main`.
- Run GitHub Actions for Python/frontend linting and formatting checks, type checks, unit tests, API/frontend integration tests, database migration validation, container builds, dependency/security scans, OpenAPI-client drift checks, and deployment-plan validation. Require CI and review approval before merging protected branches.

## Test Plan

- Unit-test every provider, strategy, broker, risk, approval, normalization, and tenant-isolation contract with deterministic fixtures.
- Run integration tests against Compose services for migrations, object storage lineage, job retries, WebSocket updates, RBAC/SSO paths, and API-client compatibility.
- Use historical replay fixtures to prove no look-ahead bias, correct corporate-action handling, realistic execution costs, idempotent orders, reconciliation recovery, risk-limit enforcement, and kill-switch behavior.
- Add frontend end-to-end tests for researcher, trader, administrator, and viewer workflows.
- Treat paper trading and broker sandbox validation as mandatory gates before any live-trading deployment can be enabled.

## Assumptions

- The platform is research and execution infrastructure, not investment advice.
- "Support all options" is implemented through configurable adapters and policies, with secure defaults rather than separate products.
- React + Vite is the sole primary UI; FastAPI remains API-first for future clients.
- Azure receives first provider-specific deployment assets; AWS and GCP remain supported through portable container/Kubernetes and provider-module hooks.
- Free/open tools and free data sources are the defaults; paid data or services remain optional, entitlement-gated extensions.
