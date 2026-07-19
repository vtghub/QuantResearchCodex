from datetime import UTC, datetime
from enum import StrEnum
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


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def enqueue(self, record: JobRecord) -> JobRecord:
        self._jobs[record.id] = record
        return record

    def list(self, tenant_id: str) -> list[JobRecord]:
        return [job for job in self._jobs.values() if job.tenant_id == tenant_id]

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    async def run_next(self) -> JobRecord | None:
        for job in self._jobs.values():
            if job.status == JobStatus.QUEUED:
                return await self.run(job.id)
        return None

    async def run(self, job_id: str) -> JobRecord:
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        job.updated_at = datetime.now(UTC)
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
        return job


def run_research_job(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "stubbed",
        "strategy": payload.get("strategy", "research-template"),
        "message": "Research execution will connect to the backtest engine phase.",
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
