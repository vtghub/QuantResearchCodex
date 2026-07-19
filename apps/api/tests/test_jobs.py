from pathlib import Path
from uuid import uuid4

import pytest
from quantresearch_api.jobs import (
    JobKind,
    JobQueue,
    JobRecord,
    JobStatus,
    JsonFileJobStore,
    build_job_store,
)


@pytest.mark.anyio
async def test_ingestion_job_runs_static_provider() -> None:
    queue = JobQueue()
    job = queue.enqueue(
        JobRecord(
            kind=JobKind.INGEST_MARKET_DATA,
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            payload={"provider": "stooq", "symbols": ["SPY"]},
        )
    )

    result = await queue.run(job.id)

    assert result.status == JobStatus.SUCCEEDED
    assert result.result["provider"] == "stooq"
    assert result.result["checksum"].startswith("sha256:")


@pytest.mark.anyio
async def test_research_job_is_queued_and_executed() -> None:
    queue = JobQueue()
    queue.enqueue(
        JobRecord(
            kind=JobKind.RUN_RESEARCH,
            tenant_id="tenant-1",
            payload={"strategy": "momentum"},
        )
    )

    result = await queue.run_next()

    assert result is not None
    assert result.status == JobStatus.SUCCEEDED
    assert result.result["strategy"] == "momentum"
    assert result.result["status"] == "completed"
    assert "equity_curve" in result.result


@pytest.mark.anyio
async def test_json_file_job_store_persists_between_queue_instances() -> None:
    store_path = Path(".quantresearch/test-state") / f"{uuid4()}.json"
    first_queue = JobQueue(JsonFileJobStore(store_path))
    job = first_queue.enqueue(
        JobRecord(
            kind=JobKind.RUN_RESEARCH,
            tenant_id="tenant-1",
            workspace_id="workspace-1",
            payload={"strategy": "durable-momentum"},
        )
    )

    await first_queue.run(job.id)

    second_queue = JobQueue(JsonFileJobStore(store_path))
    restored = second_queue.get(job.id)

    assert restored is not None
    assert restored.status == JobStatus.SUCCEEDED
    assert restored.result["strategy"] == "durable-momentum"
    store_path.unlink(missing_ok=True)


def test_job_state_summary_counts_statuses() -> None:
    queue = JobQueue()
    queue.enqueue(JobRecord(kind=JobKind.RUN_RESEARCH, tenant_id="tenant-1"))
    queue.enqueue(
        JobRecord(
            kind=JobKind.INGEST_MARKET_DATA,
            tenant_id="tenant-1",
            status=JobStatus.FAILED,
            error="boom",
        )
    )

    summary = queue.state("tenant-1")

    assert summary.backend == "memory"
    assert summary.total == 2
    assert summary.queued == 1
    assert summary.failed == 1


def test_build_job_store_selects_local_durable_backend() -> None:
    store_path = Path(".quantresearch/test-state") / f"{uuid4()}.json"
    store = build_job_store(
        "json-file",
        job_state_file=str(store_path),
        redis_url="redis://localhost:6379/0",
        database_url="postgresql://localhost/quantresearch",
    )

    assert store.backend_name == "json-file"
