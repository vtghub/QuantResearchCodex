from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from quantresearch_core.contracts import AssetClass, BrokerMode, StrategyLifecycle


class ResourceKind(StrEnum):
    WORKSPACE = "workspace"
    DATASET = "dataset"
    RESEARCH_RUN = "research_run"
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    PORTFOLIO = "portfolio"
    ORDER = "order"
    RISK_EVENT = "risk_event"
    AUDIT_RECORD = "audit_record"
    USER = "user"


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "quantresearch-api"
    environment: str
    live_trading_enabled: bool


class TenantContext(BaseModel):
    tenant_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID = Field(default_factory=uuid4)
    role: str = "platform_admin"


class ResourceSummary(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID = Field(default_factory=uuid4)
    kind: ResourceKind
    name: str
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class StrategySummary(ResourceSummary):
    lifecycle: StrategyLifecycle = StrategyLifecycle.DRAFT
    live_enabled: bool = False


class AuditRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    actor: str
    action: str
    target_kind: ResourceKind
    target_id: UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    immutable: bool = True


class ConsoleMetric(BaseModel):
    key: str
    label: str
    value: str
    detail: str


class ConsolePanel(BaseModel):
    key: str
    title: str
    description: str
    action: str
    rows: list[dict[str, str]]


class ConsoleResponse(BaseModel):
    metrics: list[ConsoleMetric]
    panels: list[ConsolePanel]
    workspace_name: str = "Default Research Workspace"
    verification_state: str = "API-backed console data loaded."


class EnqueueIngestionRequest(BaseModel):
    provider: str = "stooq"
    symbols: list[str] = Field(default_factory=lambda: ["SPY"])


class EnqueueResearchRequest(BaseModel):
    strategy: str = "research-template"
    dataset_id: str | None = None
    parameters: dict[str, str] = Field(default_factory=dict)


class RegisterUserRequest(BaseModel):
    email: str
    password: str
    display_name: str
    role: str = "researcher"


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    tenant_id: UUID
    workspace_id: UUID


class AuthProvider(BaseModel):
    name: str
    type: str
    enabled: bool
    status: str


class BrokerOrderRequest(BaseModel):
    strategy_id: UUID
    symbol: str = Field(min_length=1)
    asset_class: AssetClass = AssetClass.EQUITY
    venue: str = "SMART"
    currency: str = "USD"
    timezone: str = "America/New_York"
    side: str = Field(pattern="^(buy|sell)$")
    quantity: float = Field(gt=0)
    order_type: str = Field(pattern="^(market|limit)$")
    estimated_price: float = Field(gt=0)
    client_order_id: str = Field(min_length=8, max_length=128)
    mode: BrokerMode = BrokerMode.PAPER

    @property
    def estimated_notional(self) -> float:
        return self.quantity * self.estimated_price


class BrokerOrderResponse(BaseModel):
    broker: str
    mode: BrokerMode
    client_order_id: str
    status: str
    estimated_notional: float
    gates: list[str]


class RiskPolicySummary(BaseModel):
    tenant_id: UUID
    name: str
    status: str
    scope: str
    description: str


class KillSwitchRequest(BaseModel):
    enabled: bool
    reason: str = Field(min_length=8, max_length=512)


class KillSwitchState(BaseModel):
    tenant_id: UUID
    enabled: bool = False
    reason: str = "default-clear"
    updated_by: str = "system"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApprovalRequest(BaseModel):
    target_kind: ResourceKind
    target_id: UUID
    reason: str = Field(min_length=8, max_length=512)


class ApprovalRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    workspace_id: UUID
    target_kind: ResourceKind
    target_id: UUID
    requested_by: str
    reason: str
    status: str = "pending"
    approved_by: list[str] = Field(default_factory=list)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decided_at: datetime | None = None


class ApprovalDecisionResponse(BaseModel):
    record: ApprovalRecord
    gates: list[str]


class CreateDatasetManifestRequest(BaseModel):
    provider: str = Field(min_length=2)
    symbols: list[str] = Field(min_length=1)
    asset_class: AssetClass = AssetClass.EQUITY
    storage_uri: str = Field(pattern="^(s3|az|file|memory)://.+")
    storage_format: str = Field(pattern="^(parquet|csv|json)$")
    checksum: str = Field(pattern="^sha256:.+")
    row_count: int = Field(ge=0)
    entitlement: str = "free-first"
    transform_version: str = "raw"


class DatasetStorageManifest(BaseModel):
    id: str
    tenant_id: UUID
    workspace_id: UUID
    provider: str
    symbols: list[str]
    asset_class: AssetClass
    storage_uri: str
    storage_format: str
    checksum: str
    row_count: int
    entitlement: str
    transform_version: str
    created_at: datetime


class CreateArtifactVersionRequest(BaseModel):
    artifact_type: str = Field(pattern="^(strategy|backtest|model|report)$")
    name: str = Field(min_length=2)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    source_run_id: str | None = None
    storage_uri: str = Field(pattern="^(s3|az|file|memory)://.+")
    checksum: str = Field(pattern="^sha256:.+")
    metrics: dict[str, float] = Field(default_factory=dict)


class ArtifactVersion(BaseModel):
    id: str
    tenant_id: UUID
    workspace_id: UUID
    artifact_type: str
    name: str
    version: str
    source_run_id: str | None
    storage_uri: str
    checksum: str
    metrics: dict[str, float]
    created_at: datetime


class OpsMetricsResponse(BaseModel):
    service: str = "quantresearch-api"
    environment: str
    live_trading_enabled: bool
    job_backend: str
    jobs: dict[str, int]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditExportResponse(BaseModel):
    tenant_id: UUID
    format: str = "json"
    record_count: int
    records: list[AuditRecord]
    exported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
