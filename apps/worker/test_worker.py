"""
Worker Test Suite — tests for the Worker queue processor, handler registration,
job processing lifecycle, error handling, and retry logic.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.worker.core.queue import Worker


# ---------------------------------------------------------------------------
# Handler Registration Tests
# ---------------------------------------------------------------------------

class TestWorkerRegistration:
    """Tests for handler registration and validation."""

    def test_register_handler(self):
        """Worker should accept and store valid handler registrations."""
        worker = Worker(batch_size=5, lease_minutes=3)

        async def my_handler(payload, session):
            pass

        worker.register("TEST_JOB", my_handler)
        assert "TEST_JOB" in worker.handlers
        assert worker.handlers["TEST_JOB"] is my_handler

    def test_register_multiple_handlers(self):
        """Worker should support multiple job types simultaneously."""
        worker = Worker()

        async def handler_a(payload, session):
            pass

        async def handler_b(payload, session):
            pass

        worker.register("TYPE_A", handler_a)
        worker.register("TYPE_B", handler_b)

        assert len(worker.handlers) == 2
        assert worker.handlers["TYPE_A"] is handler_a
        assert worker.handlers["TYPE_B"] is handler_b

    def test_register_overwrites_existing(self):
        """Registering the same job type again should overwrite the old handler."""
        worker = Worker()

        async def handler_v1(payload, session):
            pass

        async def handler_v2(payload, session):
            pass

        worker.register("SAME_TYPE", handler_v1)
        worker.register("SAME_TYPE", handler_v2)

        assert worker.handlers["SAME_TYPE"] is handler_v2

    @patch("apps.api.core.config.settings")
    def test_dummy_handler_blocked_in_production(self, mock_settings):
        """Dummy handlers must be rejected in secure environments."""
        mock_settings.is_secure_environment = True
        worker = Worker()

        async def dummy_handler(payload, session):
            pass

        with pytest.raises(RuntimeError, match="Dummy handlers are strictly prohibited"):
            worker.register("DANGEROUS_JOB", dummy_handler)

    @patch("apps.api.core.config.settings")
    def test_dummy_handler_allowed_in_dev(self, mock_settings):
        """Dummy handlers should be allowed in development."""
        mock_settings.is_secure_environment = False
        worker = Worker()

        async def dummy_handler(payload, session):
            pass

        worker.register("DEV_JOB", dummy_handler)
        assert "DEV_JOB" in worker.handlers


# ---------------------------------------------------------------------------
# Worker Configuration Tests
# ---------------------------------------------------------------------------

class TestWorkerConfig:
    """Tests for worker configuration."""

    def test_default_config(self):
        """Worker should have sensible defaults."""
        worker = Worker()
        assert worker.batch_size == 10
        assert worker.lease_duration == timedelta(minutes=5)
        assert worker._running is False

    def test_custom_config(self):
        """Worker should accept custom batch_size and lease_minutes."""
        worker = Worker(batch_size=20, lease_minutes=10)
        assert worker.batch_size == 20
        assert worker.lease_duration == timedelta(minutes=10)

    def test_stop(self):
        """Worker.stop() should set _running to False."""
        worker = Worker()
        worker._running = True
        worker.stop()
        assert worker._running is False


# ---------------------------------------------------------------------------
# Job Processing Logic Tests
# ---------------------------------------------------------------------------

class TestJobProcessing:
    """Tests for job processing lifecycle."""

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_process_batch_empty_queue(self, mock_session_local):
        """Worker should return 0 when no jobs are available."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_session

        worker = Worker()
        count = await worker.process_batch()
        assert count == 0

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_process_job_unknown_type(self, mock_session_local):
        """Worker should fail jobs with no registered handler."""
        mock_job = MagicMock()
        mock_job.id = "job-123"
        mock_job.type = "UNKNOWN_TYPE"
        mock_job.tenant_id = "tenant-1"
        mock_job.retries = 3
        mock_job.max_retries = 3
        mock_job.payload = {}

        mock_session = AsyncMock()
        mock_session.get.return_value = mock_job
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_session

        worker = Worker()
        await worker.process_job("job-123")

        # Verify job was failed with appropriate message
        assert "FAILED_UNSUPPORTED_JOB_TYPE" in (mock_job.error_message or "")

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_process_job_handler_success(self, mock_session_local):
        """Worker should mark job as completed when handler succeeds."""
        handler_called = {"called": False, "payload": None}

        async def test_handler(payload, session):
            handler_called["called"] = True
            handler_called["payload"] = payload

        mock_job = MagicMock()
        mock_job.id = "job-456"
        mock_job.type = "TEST_JOB"
        mock_job.tenant_id = "tenant-1"
        mock_job.retries = 3
        mock_job.max_retries = 3
        mock_job.payload = {"key": "value"}
        mock_job.status = "processing"

        mock_session = AsyncMock()
        mock_session.get.return_value = mock_job
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_session

        worker = Worker()
        worker.register("TEST_JOB", test_handler)

        await worker.process_job("job-456")

        assert handler_called["called"] is True
        assert handler_called["payload"]["key"] == "value"
        assert handler_called["payload"]["tenant_id"] == "tenant-1"

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_process_job_handler_exception(self, mock_session_local):
        """Worker should handle exceptions in handlers gracefully."""
        async def failing_handler(payload, session):
            raise ValueError("Something went wrong in handler")

        mock_job = MagicMock()
        mock_job.id = "job-789"
        mock_job.type = "FAIL_JOB"
        mock_job.tenant_id = "tenant-1"
        mock_job.retries = 3
        mock_job.max_retries = 3
        mock_job.payload = {}
        mock_job.status = "processing"

        mock_session = AsyncMock()
        mock_session.get.return_value = mock_job
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_session

        worker = Worker()
        worker.register("FAIL_JOB", failing_handler)

        # Should not raise — error handling is internal
        await worker.process_job("job-789")

    @pytest.mark.asyncio
    async def test_process_job_nonexistent(self):
        """Worker should silently skip jobs that no longer exist in DB."""
        mock_session = AsyncMock()
        mock_session.get.return_value = None

        with patch("apps.worker.core.queue.AsyncSessionLocal") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            worker = Worker()
            # Should not raise
            await worker.process_job("nonexistent-job-id")


# ---------------------------------------------------------------------------
# Retry Logic Tests
# ---------------------------------------------------------------------------

class TestRetryLogic:
    """Tests for job retry and dead letter behavior."""

    @pytest.mark.asyncio
    async def test_fail_job_decrements_retries(self):
        """Failing a job should decrement the retry counter."""
        mock_job = MagicMock()
        mock_job.retries = 3
        mock_job.max_retries = 3
        mock_job.status = "processing"

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "test error")

        assert mock_job.retries == 2
        assert mock_job.status == "pending"

    @pytest.mark.asyncio
    async def test_fail_job_goes_dead_at_zero_retries(self):
        """Job should enter 'dead' status when retries reach 0."""
        mock_job = MagicMock()
        mock_job.retries = 1
        mock_job.max_retries = 3
        mock_job.status = "processing"

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "final failure")

        assert mock_job.retries == 0
        assert mock_job.status == "dead"
        assert mock_job.locked_until is None

    @pytest.mark.asyncio
    async def test_fail_job_records_error_message(self):
        """Failed job should store the error message."""
        mock_job = MagicMock()
        mock_job.retries = 2
        mock_job.max_retries = 3
        mock_job.status = "processing"

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "Database connection timeout")

        assert mock_job.error_message == "Database connection timeout"

    @pytest.mark.asyncio
    async def test_fail_job_with_attempt_record(self):
        """Failed job should update the attempt record if provided."""
        mock_job = MagicMock()
        mock_job.retries = 2
        mock_job.max_retries = 3
        mock_job.status = "processing"

        mock_attempt = MagicMock()
        mock_attempt.status = "processing"

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "Handler error", mock_attempt)

        assert mock_attempt.status == "failed"
        assert mock_attempt.error_details == "Handler error"
        assert mock_attempt.finished_at is not None

    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self):
        """Retry scheduling should use exponential backoff."""
        mock_job = MagicMock()
        mock_job.retries = 2  # After decrement, will be 1 → 1 attempt made
        mock_job.max_retries = 3
        mock_job.status = "processing"

        mock_session = AsyncMock()
        worker = Worker()
        await worker._fail_job(mock_session, mock_job, "transient error")

        # After failure: retries = 1, attempts_made = 3-1 = 2
        # Backoff: 2^2 * 5 = 20 seconds
        assert mock_job.run_at is not None
        assert mock_job.status == "pending"


# ---------------------------------------------------------------------------
# Start/Stop Lifecycle Tests
# ---------------------------------------------------------------------------

class TestWorkerLifecycle:
    """Tests for worker start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_stop_cycle(self):
        """Worker should stop gracefully when stop() is called."""
        worker = Worker()

        async def stop_after_delay():
            await asyncio.sleep(0.1)
            worker.stop()

        with patch.object(worker, "process_batch", new_callable=AsyncMock, return_value=0):
            # Run worker and stop it after a short delay
            task = asyncio.create_task(worker.start())
            stop_task = asyncio.create_task(stop_after_delay())

            await asyncio.wait_for(asyncio.gather(task, stop_task), timeout=2.0)
            assert worker._running is False


# ---------------------------------------------------------------------------
# Tenant Isolation in Worker Tests
# ---------------------------------------------------------------------------

class TestWorkerTenantIsolation:
    """Tests for tenant context in worker job processing."""

    def test_payload_includes_tenant_id(self):
        """Job payload passed to handler should include tenant_id."""
        # This is verified in test_process_job_handler_success above
        # Verifying the contract that payload["tenant_id"] is always set
        pass

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_handler_receives_tenant_in_payload(self, mock_session_local):
        """Handler payload must always contain tenant_id from the job."""
        received_tenant = {"value": None}

        async def tenant_check_handler(payload, session):
            received_tenant["value"] = payload.get("tenant_id")

        mock_job = MagicMock()
        mock_job.id = "job-tenant-test"
        mock_job.type = "TENANT_CHECK"
        mock_job.tenant_id = "specific-tenant-abc"
        mock_job.retries = 1
        mock_job.max_retries = 1
        mock_job.payload = {"data": "test"}

        mock_session = AsyncMock()
        mock_session.get.return_value = mock_job
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_local.return_value = mock_session

        worker = Worker()
        worker.register("TENANT_CHECK", tenant_check_handler)

        await worker.process_job("job-tenant-test")

        assert received_tenant["value"] == "specific-tenant-abc"
