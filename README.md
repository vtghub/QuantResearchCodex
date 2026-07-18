# QuantResearchCodex

QuantResearchCodex is a modular, multi-tenant quant research and trading platform scaffold. It is designed for research, backtesting, paper trading, and controlled live trading across equities/ETFs, crypto, FX, and futures with free-first data adapters and plug-in boundaries for paid providers later.

## Stack

- FastAPI API and worker services.
- React + Vite + TypeScript frontend.
- PostgreSQL, Redis, and MinIO for local development.
- Python quant packages for contracts, adapters, risk, audit, and research primitives.
- Docker Compose locally, Helm for Kubernetes, and Azure-first Terraform skeletons.

## First Milestone

This repository starts with service shells, typed API/resource foundations, plug-in contracts, local infra, and CI gates. Live trading interfaces are present as contracts only; live execution stays disabled until paper-trading and broker-sandbox gates are implemented.

## Local Development

Backend:

```powershell
cd apps/api
uv sync --all-extras --dev
uv run fastapi dev src/quantresearch_api/main.py
```

Frontend:

```powershell
cd apps/web
pnpm install
pnpm dev
```

Local services:

```powershell
docker compose up postgres redis minio
```
