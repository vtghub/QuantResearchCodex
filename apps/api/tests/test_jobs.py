import pytest
from quantresearch_api.jobs import JobKind, JobQueue, JobRecord, JobStatus


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
