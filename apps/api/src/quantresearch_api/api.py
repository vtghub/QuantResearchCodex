from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from quantresearch_api.auth import auth_service, issue_token
from quantresearch_api.brokers import BrokerSandboxGateError, broker_sandbox_service
from quantresearch_api.jobs import JobKind, JobRecord, JobStateSummary, job_queue
from quantresearch_api.risk import RiskGateError, risk_control_service
from quantresearch_api.schemas import (
    ApprovalDecisionResponse,
    ApprovalRecord,
    ApprovalRequest,
    AuditRecord,
    AuthProvider,
    AuthTokenResponse,
    BrokerOrderRequest,
    BrokerOrderResponse,
    ConsoleMetric,
    ConsolePanel,
    ConsoleResponse,
    EnqueueIngestionRequest,
    EnqueueResearchRequest,
    HealthResponse,
    KillSwitchRequest,
    KillSwitchState,
    LoginRequest,
    RegisterUserRequest,
    ResourceKind,
    ResourceSummary,
    RiskPolicySummary,
    StrategySummary,
    TenantContext,
)
from quantresearch_api.security import (
    ROLE_ORG_ADMIN,
    ROLE_PLATFORM_ADMIN,
    ROLE_RESEARCHER,
    ROLE_TRADER,
    ROLE_VIEWER,
    get_tenant_context,
    require_roles,
)
from quantresearch_api.settings import get_settings

api_router = APIRouter()
v1_router = APIRouter(prefix="/api/v1")
TenantDep = Annotated[TenantContext, Depends(get_tenant_context)]
AdminTenantDep = Annotated[
    TenantContext,
    Depends(require_roles(ROLE_PLATFORM_ADMIN, ROLE_ORG_ADMIN)),
]
ResearchTenantDep = Annotated[
    TenantContext,
    Depends(require_roles(ROLE_PLATFORM_ADMIN, ROLE_ORG_ADMIN, ROLE_RESEARCHER, ROLE_TRADER)),
]
TraderTenantDep = Annotated[
    TenantContext,
    Depends(require_roles(ROLE_PLATFORM_ADMIN, ROLE_ORG_ADMIN, ROLE_TRADER)),
]
ReadTenantDep = Annotated[
    TenantContext,
    Depends(
        require_roles(
            ROLE_PLATFORM_ADMIN,
            ROLE_ORG_ADMIN,
            ROLE_RESEARCHER,
            ROLE_TRADER,
            ROLE_VIEWER,
        )
    ),
]


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


@v1_router.get("/auth/providers", response_model=list[AuthProvider])
async def auth_providers() -> list[AuthProvider]:
    return [
        AuthProvider(name="local", type="password", enabled=True, status="active"),
        AuthProvider(name="oidc", type="oidc", enabled=False, status="configured-hook"),
        AuthProvider(name="oauth", type="oauth", enabled=False, status="configured-hook"),
    ]


@v1_router.post("/auth/register", response_model=AuthTokenResponse, status_code=201)
async def register_user(
    request: RegisterUserRequest,
    _context: AdminTenantDep,
) -> AuthTokenResponse:
    try:
        user = auth_service.register(
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            role=request.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AuthTokenResponse(
        access_token=issue_token(user),
        role=user.role,
        tenant_id=user.tenant_id,
        workspace_id=user.workspace_id,
    )


@v1_router.post("/auth/login", response_model=AuthTokenResponse)
async def login(request: LoginRequest) -> AuthTokenResponse:
    user = auth_service.authenticate(request.email, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthTokenResponse(
        access_token=issue_token(user),
        role=user.role,
        tenant_id=user.tenant_id,
        workspace_id=user.workspace_id,
    )


@v1_router.get("/workspaces", response_model=list[ResourceSummary])
async def list_workspaces(context: ReadTenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.WORKSPACE, "Default Research Workspace")]


@v1_router.get("/data/catalog", response_model=list[ResourceSummary])
async def data_catalog(context: ReadTenantDep) -> list[ResourceSummary]:
    return [
        _resource(context, ResourceKind.DATASET, "US Equities Daily Bars", "stubbed"),
        _resource(context, ResourceKind.DATASET, "Crypto Spot Daily Bars", "stubbed"),
        _resource(context, ResourceKind.DATASET, "ECB FX Reference Rates", "stubbed"),
    ]


@v1_router.get("/research/runs", response_model=list[ResourceSummary])
async def research_runs(context: ReadTenantDep) -> list[ResourceSummary]:
    return [
        _resource(
            context,
            ResourceKind.RESEARCH_RUN,
            "Momentum Baseline Walk-Forward",
            "queued",
        )
    ]


@v1_router.get("/strategies", response_model=list[StrategySummary])
async def strategies(context: ReadTenantDep) -> list[StrategySummary]:
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
async def backtests(context: ReadTenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.BACKTEST, "Event-Driven Portfolio Backtest", "stubbed")]


@v1_router.get("/portfolios", response_model=list[ResourceSummary])
async def portfolios(context: ReadTenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.PORTFOLIO, "Paper Multi-Asset Portfolio", "inactive")]


@v1_router.get("/orders", response_model=list[ResourceSummary])
async def orders(context: ReadTenantDep) -> list[ResourceSummary]:
    return [
        _resource(context, ResourceKind.ORDER, "Paper Sandbox Orders", "ready"),
        _resource(context, ResourceKind.ORDER, "Live Orders Disabled", "blocked"),
    ]


@v1_router.post(
    "/brokers/{broker_name}/paper/orders",
    response_model=BrokerOrderResponse,
    status_code=202,
)
async def submit_paper_order(
    broker_name: str,
    request: BrokerOrderRequest,
    context: TraderTenantDep,
) -> BrokerOrderResponse:
    try:
        return await broker_sandbox_service.submit_order(
            broker_name=broker_name,
            request=request,
            context=context,
            settings=get_settings(),
        )
    except BrokerSandboxGateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except RiskGateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@v1_router.get("/risk/events", response_model=list[ResourceSummary])
async def risk_events(context: ReadTenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.RISK_EVENT, "No active breaches", "clear")]


@v1_router.get("/risk/policies", response_model=list[RiskPolicySummary])
async def risk_policies(context: ReadTenantDep) -> list[RiskPolicySummary]:
    return risk_control_service.policies(context)


@v1_router.get("/risk/kill-switch", response_model=KillSwitchState)
async def risk_kill_switch(context: ReadTenantDep) -> KillSwitchState:
    return risk_control_service.kill_switch(context)


@v1_router.post("/risk/kill-switch", response_model=KillSwitchState)
async def set_risk_kill_switch(
    request: KillSwitchRequest,
    context: TraderTenantDep,
) -> KillSwitchState:
    return risk_control_service.set_kill_switch(request, context)


@v1_router.get("/risk/approvals", response_model=list[ApprovalRecord])
async def risk_approvals(context: ReadTenantDep) -> list[ApprovalRecord]:
    return risk_control_service.approvals(context)


@v1_router.post("/risk/approvals", response_model=ApprovalRecord, status_code=201)
async def request_risk_approval(
    request: ApprovalRequest,
    context: TraderTenantDep,
) -> ApprovalRecord:
    return risk_control_service.request_approval(request, context)


@v1_router.post(
    "/risk/approvals/{approval_id}/approve",
    response_model=ApprovalDecisionResponse,
)
async def approve_risk_request(
    approval_id: UUID,
    context: AdminTenantDep,
) -> ApprovalDecisionResponse:
    try:
        return risk_control_service.approve(approval_id, context)
    except RiskGateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@v1_router.get("/audit/records", response_model=list[AuditRecord])
async def audit_records(context: ReadTenantDep) -> list[AuditRecord]:
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
async def users(context: AdminTenantDep) -> list[ResourceSummary]:
    return [_resource(context, ResourceKind.USER, "Platform Admin", "active")]


@v1_router.get("/console", response_model=ConsoleResponse)
async def console(context: ReadTenantDep) -> ConsoleResponse:
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
async def jobs(context: ReadTenantDep) -> list[JobRecord]:
    return job_queue.list(str(context.tenant_id))


@v1_router.get("/jobs/state", response_model=JobStateSummary)
async def job_state(context: ReadTenantDep) -> JobStateSummary:
    return job_queue.state(str(context.tenant_id))


@v1_router.post("/jobs/ingest", response_model=JobRecord, status_code=202)
async def enqueue_ingestion(
    request: EnqueueIngestionRequest,
    context: ResearchTenantDep,
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
    context: ResearchTenantDep,
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
async def run_job(job_id: str, _context: ResearchTenantDep) -> JobRecord:
    if job_queue.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return await job_queue.run(job_id)


api_router.include_router(v1_router)
