# QuantResearchCodex

QuantResearchCodex is a multi-user quantitative research platform built for the OpenAI hackathon. It demonstrates an end-to-end Equity/ETF research workflow: fetch free online market data, inspect the exact raw rows used, mine returns, generate signals, backtest, construct a portfolio, and review the decisions made along the way.

The platform is intentionally API-first and modular, with FastAPI services, a React/Vite operator UI, reusable Python quant packages, OpenAPI client generation, and infrastructure skeletons for Docker Compose, Helm, Terraform, CI, and future durable services.

> This is research infrastructure, not investment advice. Live broker execution remains disabled by default.

## Hackathon Highlights

- **Working UI demo**: run an Equity/ETF experiment from the browser with editable filters.
- **Free-data fallback**: tries Stooq first, then Yahoo Finance-compatible chart data.
- **Full experiment transparency**: shows raw OHLCV bars, data profile, workflow steps, decisions, backtest results, and portfolio allocations.
- **Quant engine foundation**: moving-average signal generation, vectorized backtests, fees/slippage, and long-only momentum/inverse-volatility portfolio construction.
- **Governance built in**: local auth, RBAC, paper-trading sandbox gates, tenant kill switch, approval modeling, audit export, and live-trading disabled defaults.
- **Modular architecture**: plug-in boundaries for data providers, strategies, backtest engines, brokers, risk policies, and approvals.

## Demo: Equity/ETF Research Use Case

Open the UI:

```text
http://127.0.0.1:5174
```

Then:

1. Go to **Experiments**.
2. Click **Adjust filters** to edit symbols, date range, moving-average windows, fees, and slippage.
3. Click **Create research run** or the use-case card button.
4. Inspect:
   - **Data used**
   - **Complete raw data used**
   - **Steps followed**
   - **Decisions made**
   - **Backtest results**
   - **Portfolio construction**

Default demo symbols are `SPY`, `QQQ`, and `IWM`.

## How Codex And GPT-5.6 Were Used

This project was built as an AI-native engineering workflow.

- **GPT-5.6 Terra High** was used in planning mode to reshape the initial implementation plan into the approved architecture in [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md).
- **Codex** was used as the implementation agent to:
  - Bootstrap the monorepo and connect it to GitHub.
  - Build FastAPI services, React/Vite UI, Python quant packages, and generated OpenAPI contracts.
  - Implement features phase by phase on `feature/*` branches and promote them through `develop` to `main`.
  - Maintain [docs/PROJECT_MEMORY.md](docs/PROJECT_MEMORY.md) as an incremental build log and decision record.
  - Add tests, run verification, regenerate API clients, and update docs continuously.
  - Diagnose local runtime issues such as CORS and port conflicts.
- **MCP-native-core** is documented as developer-only optimization tooling, pinned in [docs/MCP_NATIVE_CORE.md](docs/MCP_NATIVE_CORE.md). It is not a production runtime dependency.

The result is a repo that preserves both the product and the AI-assisted engineering trail.

## Architecture

```text
apps/
  api/       FastAPI API, worker hook, services, schemas, tests
  web/       React + Vite + TypeScript operator UI
packages/
  quant_core      contracts, backtesting, portfolio construction
  quant_adapters  free-first data and broker adapter interfaces
infra/
  helm/ terraform/ deployment skeletons
docs/
  plans, memory, diagrams, use-case docs, runbook
```

Helpful diagrams:

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Feature Map](docs/FEATURE_MAP.md)
- [Request Flow](docs/REQUEST_FLOW.md)

## Local Run

The current local demo uses:

- API: `http://127.0.0.1:8001`
- UI: `http://127.0.0.1:5174`

Start the API:

```powershell
$env:PYTHONPATH="C:\Venu\Dev\ChatGPT\QuantResearch\apps\api\src;C:\Venu\Dev\ChatGPT\QuantResearch\packages\quant_core\src;C:\Venu\Dev\ChatGPT\QuantResearch\packages\quant_adapters\src"
.\.venv\Scripts\python.exe -m uvicorn quantresearch_api.main:app --host 127.0.0.1 --port 8001
```

Build and serve the UI:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8001"
C:\Users\Venu\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd --filter quantresearch-web build
.\.venv\Scripts\python.exe -m http.server 5174 --bind 127.0.0.1 --directory .\apps\web\dist
```

Direct API smoke:

```powershell
$body = @{
  symbols = @("SPY", "QQQ", "IWM")
  start = "20240101"
  end = "20241231"
  fast_window = 20
  slow_window = 50
  fee_bps = 1
  slippage_bps = 1
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8001/api/v1/research/use-cases/equity-etf/live-run `
  -Headers @{ "x-role" = "researcher" } `
  -ContentType "application/json" `
  -Body $body
```

## Test And Verification

Backend:

```powershell
.\.venv\Scripts\python.exe -m pytest apps/api/tests packages/quant_core/tests packages/quant_adapters/tests
.\.venv\Scripts\python.exe -m ruff check apps packages tools
```

Frontend:

```powershell
C:\Users\Venu\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd --filter quantresearch-web build
C:\Users\Venu\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd --filter quantresearch-web test
```

OpenAPI regeneration:

```powershell
.\.venv\Scripts\python.exe tools\generate_openapi_client.py
```

## Current Status

Implemented and locally verified:

- Multi-tenant FastAPI scaffold and React operator UI.
- Local auth, signed bearer tokens, OIDC/OAuth hooks, and RBAC.
- Data catalog, dataset manifests, artifact versions, and generated OpenAPI schema.
- Job queue abstraction with memory and JSON-file stores plus Redis/Postgres placeholders.
- Equity/ETF live online-data research workflow with free vendor fallback.
- Raw data inspection, experiment steps, decisions, backtest metrics, and portfolio allocation UI.
- Paper-trading sandbox gates, risk policies, kill switch, approval modeling, audit export, and ops metrics.
- GitHub branch flow: `feature/* -> develop -> main`.

Post-scaffold hardening:

- Wire real Postgres/Redis/MinIO persistence.
- Add production OIDC/OAuth providers and secret-store integration.
- Validate Docker/Helm runtime on a Docker-enabled machine.
- Expand strategy library, data vendors, experiment comparison, and portfolio optimization methods.

## Important Docs

- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Project Memory](docs/PROJECT_MEMORY.md)
- [Equity/ETF Use Case](docs/USE_CASE_EQUITY_ETF_LIVE_RESEARCH.md)
- [Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)
- [MCP-native-core Notes](docs/MCP_NATIVE_CORE.md)
