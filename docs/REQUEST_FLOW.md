# Request Flow Diagram

This document shows how common requests move through the current system.

## UI Console Hydration

```mermaid
sequenceDiagram
  actor User
  participant Browser as React SPA
  participant Client as Generated TS Client
  participant API as FastAPI
  participant RBAC as Tenant Context/RBAC
  participant Services as Console Services

  User->>Browser: Open local web UI
  Browser->>Client: getConsole()
  Client->>API: GET /api/v1/console with x-role header
  API->>RBAC: Build tenant/workspace/role context
  RBAC-->>API: TenantContext
  API->>Services: Compose metrics and panels
  Services-->>API: ConsoleResponse
  API-->>Client: JSON payload
  Client-->>Browser: Typed console data
  Browser-->>User: Render dashboard panels

  alt API unavailable
    Browser-->>User: Render static fallback payload
  end
```

## Authenticated API Request

```mermaid
sequenceDiagram
  actor User
  participant API as FastAPI
  participant Auth as LocalAuthService
  participant Token as Signed Bearer Token
  participant RBAC as RBAC Dependency
  participant Route as Protected Route

  User->>API: POST /api/v1/auth/login
  API->>Auth: Authenticate email/password
  Auth-->>API: LocalUser
  API->>Token: Issue signed token
  API-->>User: AuthTokenResponse
  User->>API: Protected request with Authorization header
  API->>Token: Decode and verify token
  Token-->>RBAC: tenant_id, workspace_id, role
  RBAC->>Route: Allow if role is permitted
  Route-->>User: Response
```

## Research Job Flow

```mermaid
sequenceDiagram
  actor Researcher
  participant API as FastAPI
  participant RBAC as Research Role Gate
  participant Queue as JobQueue
  participant Store as JobStore
  participant Worker as Worker Runner
  participant Adapters as Market Data Adapters
  participant Engine as Backtest Engine

  Researcher->>API: POST /api/v1/jobs/research
  API->>RBAC: Require researcher/trader/admin
  RBAC-->>API: Allowed
  API->>Queue: enqueue(JobRecord)
  Queue->>Store: put queued job
  API-->>Researcher: 202 JobRecord

  Worker->>Queue: run_next()
  Queue->>Store: list queued jobs
  Queue->>Store: put running job
  Worker->>Engine: run_vector_backtest()
  Engine-->>Worker: Metrics and equity curve
  Worker->>Store: put succeeded job
```

## Paper Order Flow

```mermaid
sequenceDiagram
  actor Trader
  participant API as FastAPI
  participant RBAC as Trader/Admin Gate
  participant Risk as RiskControlService
  participant BrokerSvc as BrokerSandboxService
  participant Adapter as Broker Adapter
  participant Audit as Audit Trail

  Trader->>API: POST /api/v1/brokers/{broker}/paper/orders
  API->>RBAC: Require trader/admin
  RBAC-->>API: Allowed
  API->>BrokerSvc: submit_order()
  BrokerSvc->>Risk: ensure_execution_allowed()
  Risk-->>BrokerSvc: kill-switch-clear
  BrokerSvc->>BrokerSvc: Validate paper mode, notional cap, idempotency
  BrokerSvc->>Adapter: submit_order(OrderIntent)
  Adapter-->>BrokerSvc: accepted-paper
  BrokerSvc-->>API: BrokerOrderResponse with gates
  API-->>Trader: 202 accepted-paper
  BrokerSvc-. future .->Audit: record execution event

  alt Kill switch enabled
    Risk-->>BrokerSvc: blocked
    BrokerSvc-->>API: RiskGateError
    API-->>Trader: 423 Locked
  end

  alt Live mode requested
    BrokerSvc-->>API: BrokerSandboxGateError
    API-->>Trader: 403 Forbidden
  end
```

## Deployment Flow

```mermaid
flowchart LR
  Feature["feature/* branch"] --> Tests["Local tests and generated OpenAPI"]
  Tests --> PushFeature["Push feature branch"]
  PushFeature --> Develop["Fast-forward to develop"]
  Develop --> CI["GitHub Actions validation"]
  CI --> Main["Promote develop to main"]
  Main --> Package["Container / Helm / Terraform artifacts"]
  Package --> Deploy["Environment deployment"]

  CI -. includes .-> Backend["Pytest + Ruff"]
  CI -. includes .-> Frontend["TypeScript + Vite + Vitest"]
  CI -. includes .-> Drift["OpenAPI drift check"]
  CI -. includes .-> Infra["Compose/Helm/Terraform checks"]
```
