# QuantResearchCodex Deployment Runbook

## Local Verification

- Backend tests: `.\.venv\Scripts\python.exe -m pytest apps/api/tests packages/quant_core/tests packages/quant_adapters/tests`
- Backend lint: `.\.venv\Scripts\python.exe -m ruff check apps packages tools`
- OpenAPI regeneration: `.\.venv\Scripts\python.exe tools\generate_openapi_client.py`
- Frontend build: `pnpm --filter quantresearch-web build`
- Frontend tests: `pnpm --filter quantresearch-web test`

## Runtime Modes

- Default API mode uses in-memory job, auth, risk, catalog, and audit services for fast local development.
- `QUANTRESEARCH_JOB_STORE_BACKEND=json-file` enables local durable job state through `QUANTRESEARCH_JOB_STATE_FILE`.
- Redis and Postgres job-store classes are contract placeholders until the real backing clients are wired.
- Live trading remains disabled by default and broker order submission is paper-only until approvals and environment gates pass.

## Deployment Gates

- Feature branches must be promoted through `feature/*` to `develop` to `main`.
- Generated OpenAPI output must be committed with any API contract change.
- Docker Compose and Helm remain deployment skeletons; validate Compose once Docker is available on the operator machine.
- Secrets, broker credentials, and vendor tokens must stay outside repository files and project memory.

## Operational Checks

- API health: `GET /health`
- Service metrics: `GET /api/v1/ops/metrics`
- Job state: `GET /api/v1/jobs/state`
- Audit export: `GET /api/v1/audit/export`
- Risk state: `GET /api/v1/risk/kill-switch`
