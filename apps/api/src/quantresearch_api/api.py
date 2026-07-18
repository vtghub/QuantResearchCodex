from typing import Annotated

from fastapi import APIRouter, Depends

from quantresearch_api.schemas import (
    AuditRecord,
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


api_router.include_router(v1_router)
