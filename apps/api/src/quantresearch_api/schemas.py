from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from quantresearch_core.contracts import StrategyLifecycle


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
