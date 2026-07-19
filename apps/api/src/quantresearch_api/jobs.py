import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field
from quantresearch_adapters.market_data import (
    CoinGeckoProvider,
    EcbFxProvider,
    FredProvider,
    StooqProvider,
    YahooFinanceCompatibleProvider,
)
from quantresearch_core.backtesting import (
    BacktestInput,
    moving_average_signals,
    returns_from_prices,
    run_vector_backtest,
)


class JobKind(StrEnum):
    INGEST_MARKET_DATA = "ingest_market_data"
    RUN_RESEARCH = "run_research"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: JobKind
    status: JobStatus = JobStatus.QUEUED
    tenant_id: str
    workspace_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class JobStateSummary(BaseModel):
    backend: str
    total: int
    queued: int
    running: int
    succeeded: int
    failed: int


class JobStoreUnavailable(RuntimeError):
    """Raised when a configured durable job store cannot be reached."""


class JobStore:
    backend_name = "abstract"

    def put(self, record: JobRecord) -> JobRecord:
        raise NotImplementedError

    def list(self, tenant_id: str | None = None) -> list[JobRecord]:
        raise NotImplementedError

    def get(self, job_id: str) -> JobRecord | None:
        raise NotImplementedError


class InMemoryJobStore(JobStore):
    backend_name = "memory"

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def put(self, record: JobRecord) -> JobRecord:
        self._jobs[record.id] = record
        return record

    def list(self, tenant_id: str | None = None) -> list[JobRecord]:
        jobs = list(self._jobs.values())
        if tenant_id is None:
            return jobs
        return [job for job in jobs if job.tenant_id == tenant_id]

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)


class JsonFileJobStore(JobStore):
    backend_name = "json-file"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def put(self, record: JobRecord) -> JobRecord:
        jobs = {job.id: job for job in self.list()}
        jobs[record.id] = record
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                [job.model_dump(mode="json") for job in jobs.values()],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return record

    def list(self, tenant_id: str | None = None) -> list[JobRecord]:
        if not self.path.exists():
            return []
        records = [
            JobRecord.model_validate(item)
            for item in json.loads(self.path.read_text(encoding="utf-8"))
        ]
        if tenant_id is None:
            return records
        return [job for job in records if job.tenant_id == tenant_id]

    def get(self, job_id: str) -> JobRecord | None:
        return next((job for job in self.list() if job.id == job_id), None)


class RedisJobStore(JobStore):
    backend_name = "redis"

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url

    def _unavailable(self) -> None:
        raise JobStoreUnavailable("Redis job store is configured but not connected yet.")

    def put(self, record: JobRecord) -> JobRecord:
        self._unavailable()

    def list(self, tenant_id: str | None = None) -> list[JobRecord]:
        self._unavailable()

    def get(self, job_id: str) -> JobRecord | None:
        self._unavailable()


class PostgresJobStore(JobStore):
    backend_name = "postgres"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _unavailable(self) -> None:
        raise JobStoreUnavailable("Postgres job store is configured but not connected yet.")

    def put(self, record: JobRecord) -> JobRecord:
        self._unavailable()

    def list(self, tenant_id: str | None = None) -> list[JobRecord]:
        self._unavailable()

    def get(self, job_id: str) -> JobRecord | None:
        self._unavailable()


class JobQueue:
    def __init__(self, store: JobStore | None = None) -> None:
        self.store = store or InMemoryJobStore()

    def enqueue(self, record: JobRecord) -> JobRecord:
        return self.store.put(record)

    def list(self, tenant_id: str) -> list[JobRecord]:
        return self.store.list(tenant_id)

    def get(self, job_id: str) -> JobRecord | None:
        return self.store.get(job_id)

    def state(self, tenant_id: str | None = None) -> JobStateSummary:
        jobs = self.store.list(tenant_id)
        return JobStateSummary(
            backend=self.store.backend_name,
            total=len(jobs),
            queued=sum(job.status == JobStatus.QUEUED for job in jobs),
            running=sum(job.status == JobStatus.RUNNING for job in jobs),
            succeeded=sum(job.status == JobStatus.SUCCEEDED for job in jobs),
            failed=sum(job.status == JobStatus.FAILED for job in jobs),
        )

    async def run_next(self) -> JobRecord | None:
        for job in sorted(self.store.list(), key=lambda queued: queued.created_at):
            if job.status == JobStatus.QUEUED:
                return await self.run(job.id)
        return None

    async def run(self, job_id: str) -> JobRecord:
        job = self.store.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now(UTC)
        self.store.put(job)
        try:
            if job.kind == JobKind.INGEST_MARKET_DATA:
                job.result = await run_ingestion_job(job.payload)
            else:
                job.result = run_research_job(job.payload)
            job.status = JobStatus.SUCCEEDED
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        finally:
            job.updated_at = datetime.now(UTC)
            self.store.put(job)
        return job


def build_job_store(
    backend: str,
    *,
    job_state_file: str,
    redis_url: str,
    database_url: str,
) -> JobStore:
    normalized = backend.lower()
    if normalized == "memory":
        return InMemoryJobStore()
    if normalized in {"json", "json-file", "file"}:
        return JsonFileJobStore(job_state_file)
    if normalized == "redis":
        return RedisJobStore(redis_url)
    if normalized in {"postgres", "postgresql"}:
        return PostgresJobStore(database_url)
    raise ValueError(f"Unsupported job store backend: {backend}")


def run_research_job(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("use_case") == "equity_etf_live_research":
        from quantresearch_api.equity_etf_research import equity_etf_research_service
        from quantresearch_api.schemas import EquityEtfResearchRequest, TenantContext
        from quantresearch_api.security import DEFAULT_TENANT_ID, DEFAULT_WORKSPACE_ID

        request = EquityEtfResearchRequest.model_validate(payload)
        context = TenantContext(
            tenant_id=payload.get("tenant_id") or DEFAULT_TENANT_ID,
            workspace_id=payload.get("workspace_id") or DEFAULT_WORKSPACE_ID,
            role="researcher",
        )
        return equity_etf_research_service.run(request, context).model_dump(mode="json")

    prices = [float(value) for value in payload.get("prices", [100, 101, 103, 102, 105, 107])]
    fast_window = int(payload.get("fast_window", 2))
    slow_window = int(payload.get("slow_window", 3))
    signals = moving_average_signals(prices, fast_window=fast_window, slow_window=slow_window)
    result = run_vector_backtest(
        BacktestInput(
            returns=returns_from_prices(prices),
            signals=signals[1:],
            fee_bps=float(payload.get("fee_bps", 1.0)),
            slippage_bps=float(payload.get("slippage_bps", 1.0)),
        )
    )
    return {
        "status": "completed",
        "strategy": payload.get("strategy", "research-template"),
        "total_return": result.total_return,
        "annualized_return": result.annualized_return,
        "annualized_volatility": result.annualized_volatility,
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "turnover": result.turnover,
        "equity_curve": result.equity_curve,
    }


async def run_ingestion_job(payload: dict[str, Any]) -> dict[str, Any]:
    provider_name = str(payload.get("provider", "stooq"))
    symbols = list(payload.get("symbols", ["SPY"]))
    provider = build_provider(provider_name, symbols)
    instruments = await provider.discover()
    manifest = await provider.ingest(symbols)
    return {
        "dataset_id": manifest.dataset_id,
        "provider": manifest.provider,
        "symbols": list(manifest.symbols),
        "checksum": manifest.checksum,
        "instrument_count": len(instruments),
        "entitlement": manifest.entitlement,
    }


def build_provider(provider_name: str, symbols: list[str]):
    providers = {
        "coingecko": CoinGeckoProvider,
        "ecb-fx": EcbFxProvider,
        "fred": FredProvider,
        "stooq": StooqProvider,
        "yahoo-finance-compatible": YahooFinanceCompatibleProvider,
    }
    try:
        provider_type = providers[provider_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider_name}") from exc
    return provider_type(symbols=symbols)


job_queue = JobQueue()
