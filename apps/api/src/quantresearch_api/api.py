from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from quantresearch_api.jobs import JobKind, JobRecord, job_queue
from quantresearch_api.schemas import (
    AuditRecord,
    ConsoleMetric,
    ConsolePanel,
    ConsoleResponse,
    EnqueueIngestionRequest,
    EnqueueResearchRequest,
    HealthResponse,
    ResourceKind,
    ResourceSummary,
    StrategySummary,
    TenantContext,
)
from quantresearch_api.security import get_tenant_context
from quantresearch_api.settings import get_settings

api_router = APIRouter()
v1_router = APIRouter(prefix="/api/v1")
TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]


@api_router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        environment=settings.env,
        live_trading_enabled=settings.live_trading_enabled,
    )


def _resource(
    context: TenantContext,
    kind: ResourceKind,
    name: str,
    status: str = "ready",
) -> ResourceSummary:
    return ResourceSummary(
        tenant_id=context.tenant_id,
        workspace_id=context.workspace_id,
        kind=kind,
        name=name,
        status=status,
    )


@v1_router.get("/identity/me", response_model=TenantContext)
async def identity_me(context: TenantDep) -> TenantContext:
    return context


@v1_router.get("/workspaces", response_model=list[ResourceSummary])
async def list_workspaces(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.WORKSPACE, "Default Research Workspace")]


@v1_router.get("/data/catalog", response_model=list[ResourceSummary])
async def data_catalog(context: TenantDep) -> list[ResourceSummary]:
    return [
        _resource(context, ResourceKind.DATASET, "US Equities Daily Bars", "stubbed"),
        _resource(context, ResourceKind.DATASET, "Crypto Spot Daily Bars", "stubbed"),
        _resource(context, ResourceKind.DATASET, "ECB FX Reference Rates", "stubbed"),
    ]


@v1_router.get("/research/runs", response_model=list[ResourceSummary])
async def research_runs(context: TenantDep) -> list[ResourceSummary]:
    return [
        _resource(
            context,
            ResourceKind.RESEARCH_RUN,
            "Momentum Baseline Walk-Forward",
            "queued",
        )
    ]


@v1_router.get("/strategies", response_model=list[StrategySummary])
async def strategies(context: TenantDep) -> list[StrategySummary]:
    return [
        StrategySummary(
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            kind=ResourceKind.STRATEGY,
            name="Cross-Asset Momentum Template",
            status="draft",
        )
    ]


@v1_router.get("/backtests", response_model=list[ResourceSummary])
async def backtests(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.BACKTEST, "Event-Driven Portfolio Backtest", "stubbed")]


@v1_router.get("/portfolios", response_model=list[ResourceSummary])
async def portfolios(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.PORTFOLIO, "Paper Multi-Asset Portfolio", "inactive")]


@v1_router.get("/orders", response_model=list[ResourceSummary])
async def orders(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.ORDER, "Live Orders Disabled", "blocked")]


@v1_router.get("/risk/events", response_model=list[ResourceSummary])
async def risk_events(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.RISK_EVENT, "No active breaches", "clear")]


@v1_router.get("/audit/records", response_model=list[AuditRecord])
async def audit_records(context: TenantDep) -> list[AuditRecord]:
    target = _resource(context, ResourceKind.WORKSPACE, "Default Research Workspace")
    return [
        AuditRecord(
            tenant_id=context.tenant_id,
            actor="system",
            action="bootstrap.scaffold",
            target_kind=target.kind,
            target_id=target.id,
        )
    ]


@v1_router.get("/admin/users", response_model=list[ResourceSummary])
async def users(context: TenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.USER, "Platform Admin", "active")]


@v1_router.get("/console", response_model=ConsoleResponse)
async def console(context: TenantDep) -> ConsoleResponse:
    return ConsoleResponse(
        metrics=[
            ConsoleMetric(key="data", label="Data Health", value="3", detail="adapters ready"),
            ConsoleMetric(key="experiments", label="Experiments", value="1", detail="queued run"),
            ConsoleMetric(
                key="strategies",
                label="Strategies",
                value="draft",
                detail="lifecycle gated",
            ),
            ConsoleMetric(
                key="portfolios",
                label="Portfolios",
                value="paper",
                detail="live disabled",
            ),
            ConsoleMetric(key="risk", label="Risk", value="clear", detail="limits modeled"),
            ConsoleMetric(key="audit", label="Audit", value="append-only", detail="events tracked"),
            ConsoleMetric(key="users", label="Users", value="RBAC", detail="tenant scoped"),
        ],
        panels=[
            ConsolePanel(
                key="data",
                title="Market data catalog",
                description=(
                    "Track free-first adapters, asset coverage, provenance, "
                    "and entitlement status."
                ),
                action="Run ingestion check",
                rows=[
                    {
                        "Source": "Stooq",
                        "Asset": "Equities/ETFs",
                        "State": "Ready",
                        "Provenance": "Required",
                    },
                    {
                        "Source": "CoinGecko",
                        "Asset": "Crypto",
                        "State": "Ready",
                        "Provenance": "Required",
                    },
                    {"Source": "ECB FX", "Asset": "FX", "State": "Ready", "Provenance": "Required"},
                ],
            ),
            ConsolePanel(
                key="experiments",
                title="Research runs",
                description=(
                    "Compare queued and draft experiments before they become "
                    "strategy candidates."
                ),
                action="Create research run",
                rows=[
                    {
                        "Run": "Momentum Baseline",
                        "Dataset": "US Equities Daily",
                        "State": "Queued",
                        "Gate": "No leak checks",
                    },
                    {
                        "Run": "Crypto Trend",
                        "Dataset": "Crypto Spot Daily",
                        "State": "Draft",
                        "Gate": "Needs costs",
                    },
                ],
            ),
            ConsolePanel(
                key="strategies",
                title="Strategy lifecycle",
                description=(
                    "Promote strategies through research, paper approval, "
                    "and live approval gates."
                ),
                action="Open promotion queue",
                rows=[
                    {
                        "Strategy": "Cross-Asset Momentum",
                        "Lifecycle": "Draft",
                        "Approval": "Two-person",
                        "Live": "Disabled",
                    },
                    {
                        "Strategy": "Mean Reversion Template",
                        "Lifecycle": "Draft",
                        "Approval": "Owner",
                        "Live": "Disabled",
                    },
                ],
            ),
            ConsolePanel(
                key="portfolios",
                title="Portfolio monitor",
                description=(
                    "Watch paper portfolios first; live execution remains "
                    "blocked by design."
                ),
                action="Run reconciliation",
                rows=[
                    {
                        "Portfolio": "Paper Multi-Asset",
                        "Mode": "Paper",
                        "Exposure": "$0",
                        "Reconcile": "Pending",
                    },
                    {
                        "Portfolio": "Live Sandbox",
                        "Mode": "Live",
                        "Exposure": "$0",
                        "Reconcile": "Blocked",
                    },
                ],
            ),
            ConsolePanel(
                key="risk",
                title="Risk controls",
                description=(
                    "Centralize kill switches, notional limits, approval modes, "
                    "and policy state."
                ),
                action="Review policies",
                rows=[
                    {
                        "Policy": "Live Kill Switch",
                        "Status": "On",
                        "Limit": "All live orders blocked",
                        "Scope": "Platform",
                    },
                    {
                        "Policy": "Max Notional",
                        "Status": "Draft",
                        "Limit": "$0 until configured",
                        "Scope": "Tenant",
                    },
                ],
            ),
            ConsolePanel(
                key="audit",
                title="Audit history",
                description=(
                    "Inspect append-only platform events for governance "
                    "and reproducibility."
                ),
                action="Export audit view",
                rows=[
                    {
                        "Event": "bootstrap.scaffold",
                        "Actor": "system",
                        "Target": "workspace",
                        "Immutability": "Modeled",
                    },
                    {
                        "Event": "ui.navigation.enabled",
                        "Actor": "system",
                        "Target": "web",
                        "Immutability": "Committed",
                    },
                ],
            ),
            ConsolePanel(
                key="users",
                title="Users and workspaces",
                description=(
                    "Manage tenant-scoped roles for platform admins, "
                    "researchers, traders, and viewers."
                ),
                action="Invite user",
                rows=[
                    {
                        "User": "Platform Admin",
                        "Role": context.role,
                        "Tenant": "default",
                        "Status": "Active",
                    },
                    {
                        "User": "Researcher",
                        "Role": "researcher",
                        "Tenant": "default",
                        "Status": "Template",
                    },
                ],
            ),
        ],
    )


@v1_router.get("/jobs", response_model=list[JobRecord])
async def jobs(context: TenantDep) -> list[JobRecord]:
    return job_queue.list(str(context.tenant_id))


@v1_router.post("/jobs/ingest", response_model=JobRecord, status_code=202)
async def enqueue_ingestion(
    request: EnqueueIngestionRequest,
    context: TenantDep,
) -> JobRecord:
    return job_queue.enqueue(
        JobRecord(
            kind=JobKind.INGEST_MARKET_DATA,
            tenant_id=str(context.tenant_id),
            workspace_id=str(context.workspace_id),
            payload=request.model_dump(),
        )
    )


@v1_router.post("/jobs/research", response_model=JobRecord, status_code=202)
async def enqueue_research(
    request: EnqueueResearchRequest,
    context: TenantDep,
) -> JobRecord:
    return job_queue.enqueue(
        JobRecord(
            kind=JobKind.RUN_RESEARCH,
            tenant_id=str(context.tenant_id),
            workspace_id=str(context.workspace_id),
            payload=request.model_dump(),
        )
    )


@v1_router.post("/jobs/{job_id}/run", response_model=JobRecord)
async def run_job(job_id: str) -> JobRecord:
    if job_queue.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return await job_queue.run(job_id)


api_router.include_router(v1_router)
