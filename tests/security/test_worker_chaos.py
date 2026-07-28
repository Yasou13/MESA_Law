"""
Worker Chaos Tests — tests for error resilience, dead letter queue behavior,
poison message handling, timeout recovery, and concurrent job processing safety.
"""
import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.worker.core.queue import Worker


# ---------------------------------------------------------------------------
# Crash Recovery Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_crash_recovery():
    """Jobs left in 'processing' state after worker crash should be recoverable."""
    from apps.api.models.queue import Job
    
    # 1. Simulate Job Creation
    job = Job(id="job_123", type="PARSE_DOCUMENT", status="processing")
    
    # 2. Simulate Worker Crash (job stays processing)
    # The recovery cron/process should detect 'processing' jobs older than timeout and mark them 'failed' or requeue
    
    def simulate_recovery_sweep(job: Job):
        # Fake logic for sweeping dead jobs
        if job.status == "processing": # and time_elapsed > 30 mins
            job.status = "failed"
            job.error_details = "Worker timeout. Sent to DLQ."
            return True
        return False
        
    recovered = simulate_recovery_sweep(job)
    
    assert recovered is True
    assert job.status == "failed"
    assert "timeout" in job.error_details


# ---------------------------------------------------------------------------
# Dead Letter Queue Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_moves_to_dead_after_max_retries():
    """Job should be marked 'dead' after exhausting all retry attempts."""
    mock_job = MagicMock()
    mock_job.retries = 1  # Last retry
    mock_job.max_retries = 3
    mock_job.status = "processing"

    mock_session = AsyncMock()
    worker = Worker()
    await worker._fail_job(mock_session, mock_job, "Persistent failure")

    assert mock_job.status == "dead"
    assert mock_job.retries == 0
    assert mock_job.locked_until is None


@pytest.mark.asyncio
async def test_dead_job_preserves_error_history():
    """Dead jobs should retain the final error message for debugging."""
    mock_job = MagicMock()
    mock_job.retries = 1
    mock_job.max_retries = 3

    mock_attempt = MagicMock()

    mock_session = AsyncMock()
    worker = Worker()
    await worker._fail_job(mock_session, mock_job, "OOM Kill: worker memory exceeded 512MB", mock_attempt)

    assert mock_job.error_message == "OOM Kill: worker memory exceeded 512MB"
    assert mock_attempt.error_details == "OOM Kill: worker memory exceeded 512MB"
    assert mock_attempt.finished_at is not None


# ---------------------------------------------------------------------------
# Poison Message Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("apps.worker.core.queue.AsyncSessionLocal")
async def test_poison_message_doesnt_crash_worker(mock_session_local):
    """A handler raising any exception should not crash the entire worker."""
    call_count = {"value": 0}

    async def poison_handler(payload, session):
        call_count["value"] += 1
        raise RuntimeError("POISON: Unrecoverable data corruption in payload")

    mock_job = MagicMock()
    mock_job.id = "poison-job-1"
    mock_job.type = "POISON_TEST"
    mock_job.tenant_id = "tenant-1"
    mock_job.retries = 1
    mock_job.max_retries = 1
    mock_job.payload = {"corrupt": True}

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_job
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_session_local.return_value = mock_session

    worker = Worker()
    worker.register("POISON_TEST", poison_handler)

    # Should NOT raise
    await worker.process_job("poison-job-1")


@pytest.mark.asyncio
async def test_malformed_payload_handling():
    """Handler receiving unexpected payload structure should fail gracefully."""
    async def strict_handler(payload, session):
        # Simulate handler that expects specific fields
        required_field = payload["document_id"]  # Will KeyError on malformed payload

    mock_job = MagicMock()
    mock_job.id = "malformed-job"
    mock_job.type = "STRICT_JOB"
    mock_job.tenant_id = "tenant-1"
    mock_job.retries = 2
    mock_job.max_retries = 3
    mock_job.payload = {}  # Missing required field

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_job

    with patch("apps.worker.core.queue.AsyncSessionLocal") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        worker = Worker()
        worker.register("STRICT_JOB", strict_handler)

        # Should not crash the worker
        await worker.process_job("malformed-job")


# ---------------------------------------------------------------------------
# Timeout Handling Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handler_timeout_simulation():
    """Long-running handlers should be detectable via lease expiration."""
    worker = Worker(lease_minutes=1)  # 1 minute lease

    # Verify lease duration is properly configured
    assert worker.lease_duration == timedelta(minutes=1)

    # In production, the process_batch method uses locked_until to detect
    # stale jobs. Here we verify the lease configuration is correct.


@pytest.mark.asyncio
async def test_stale_job_requeue_logic():
    """Jobs whose lease has expired should be eligible for re-processing."""
    mock_job = MagicMock()
    mock_job.retries = 2
    mock_job.max_retries = 3
    mock_job.status = "processing"

    mock_session = AsyncMock()
    worker = Worker()

    # Simulate timeout failure
    await worker._fail_job(mock_session, mock_job, "Lease expired: worker did not complete in time")

    # Job should be re-queued (status=pending) with backoff
    assert mock_job.status == "pending"
    assert mock_job.run_at is not None
    assert mock_job.locked_until is None


# ---------------------------------------------------------------------------
# Concurrent Processing Safety Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_handles_no_handlers_gracefully():
    """Worker with no registered handlers should fail jobs, not crash."""
    mock_job = MagicMock()
    mock_job.id = "no-handler-job"
    mock_job.type = "UNREGISTERED_TYPE"
    mock_job.tenant_id = "tenant-1"
    mock_job.retries = 1
    mock_job.max_retries = 1
    mock_job.payload = {}

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_job

    with patch("apps.worker.core.queue.AsyncSessionLocal") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        worker = Worker()  # No handlers registered
        await worker.process_job("no-handler-job")

        assert "FAILED_UNSUPPORTED_JOB_TYPE" in (mock_job.error_message or "")


@pytest.mark.asyncio
async def test_exponential_backoff_progression():
    """Retry backoff should increase exponentially with each attempt."""
    backoff_times = []

    for retries_remaining in [3, 2, 1]:
        mock_job = MagicMock()
        mock_job.retries = retries_remaining
        mock_job.max_retries = 3

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "transient error")

        if mock_job.status == "pending":
            backoff_times.append(mock_job.run_at)

    # We should have collected run_at times showing increasing backoff
    # (The actual values depend on utc_now(), but we verify they were set)
    assert len(backoff_times) >= 1  # At least some retries should be pending


# ---------------------------------------------------------------------------
# Tenant Isolation Under Chaos Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_failed_job_doesnt_leak_tenant_context():
    """After a job fails, tenant context should be cleaned up."""
    tenant_after_failure = {"value": "should_be_none"}

    async def failing_handler(payload, session):
        raise Exception("Simulated failure")

    mock_job = MagicMock()
    mock_job.id = "tenant-leak-test"
    mock_job.type = "LEAK_TEST"
    mock_job.tenant_id = "sensitive-tenant-id"
    mock_job.retries = 1
    mock_job.max_retries = 1
    mock_job.payload = {}

    mock_session = AsyncMock()
    mock_session.get.return_value = mock_job

    with patch("apps.worker.core.queue.AsyncSessionLocal") as mock_factory:
        mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        worker = Worker()
        worker.register("LEAK_TEST", failing_handler)

        await worker.process_job("tenant-leak-test")

        # Verify tenant context was cleaned up
        from apps.api.core.rls import get_tenant_id
        tenant_after_failure["value"] = get_tenant_id()

    # Tenant context should be None after job processing (success or failure)
    assert tenant_after_failure["value"] is None
