from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID


class AssetClass(StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    CRYPTO = "crypto"
    FX = "fx"
    FUTURE = "future"


class BrokerMode(StrEnum):
    PAPER = "paper"
    LIVE = "live"


class StrategyLifecycle(StrEnum):
    DRAFT = "draft"
    RESEARCH_VALIDATED = "research-validated"
    PAPER_APPROVED = "paper-approved"
    LIVE_APPROVED = "live-approved"
    PAUSED = "paused"
    RETIRED = "retired"


class ApprovalMode(StrEnum):
    TWO_PERSON = "two-person"
    OWNER = "owner"
    AUTOMATED = "automated"


@dataclass(frozen=True)
class Instrument:
    symbol: str
    asset_class: AssetClass
    venue: str
    currency: str
    timezone: str
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetManifest:
    dataset_id: str
    provider: str
    created_at: datetime
    symbols: Sequence[str]
    checksum: str
    terms_url: str | None = None
    entitlement: str = "free-first"
    transform_version: str = "raw"


@dataclass(frozen=True)
class StrategyManifest:
    name: str
    version: str
    lifecycle: StrategyLifecycle
    parameters: Mapping[str, Any]
    required_features: Sequence[str]
    artifact_uri: str | None = None


@dataclass(frozen=True)
class OrderIntent:
    tenant_id: UUID
    workspace_id: UUID
    strategy_id: UUID
    instrument: Instrument
    side: str
    quantity: float
    order_type: str
    client_order_id: str
    mode: BrokerMode


class DataProvider(Protocol):
    name: str

    async def discover(self) -> Sequence[Instrument]:
        """Return instruments available through this provider."""

    async def ingest(self, symbols: Sequence[str]) -> DatasetManifest:
        """Ingest and normalize market data with provenance."""


class Strategy(Protocol):
    manifest: StrategyManifest

    async def generate_signals(self, dataset: DatasetManifest) -> Mapping[str, Any]:
        """Generate deterministic signals from a versioned dataset."""


class BacktestEngine(Protocol):
    name: str

    async def run(self, strategy: StrategyManifest, dataset: DatasetManifest) -> Mapping[str, Any]:
        """Run a reproducible backtest and return metrics/artifact references."""


class Broker(Protocol):
    name: str
    mode: BrokerMode

    async def submit_order(self, order: OrderIntent) -> Mapping[str, Any]:
        """Submit an idempotent paper or live order."""

    async def reconcile(self) -> Mapping[str, Any]:
        """Reconcile account state, orders, positions, and fills."""


class RiskPolicy(Protocol):
    name: str

    async def evaluate_order(self, order: OrderIntent) -> Mapping[str, Any]:
        """Evaluate notional, concentration, loss, approval, and kill-switch limits."""
