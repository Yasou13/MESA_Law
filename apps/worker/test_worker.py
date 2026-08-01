"""Fail-closed unit tests for the durable PostgreSQL worker."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.rls import get_tenant_id
from apps.api.core.utils import utc_now
from apps.api.models.queue import Job, JobAttempt, JobStatus
from apps.worker.core.queue import Worker
from apps.worker.jobs import TerminalJobError, validate_job_payload
from pydantic import ValidationError


def make_job(
    *,
    job_type: str = "BUILD_LEXICAL_INDEX",
    payload: dict | None = None,
    attempts_made: int = 0,
    max_retries: int = 3,
) -> Job:
    return Job(
        id="job-1",
        type=job_type,
        payload=payload if payload is not None else {"matter_id": "matter-1"},
        status=JobStatus.RUNNING,
        tenant_id="tenant-1",
        matter_id="matter-1",
        max_retries=max_retries,
        retries=max_retries - attempts_made,
        attempts_made=attempts_made,
        run_at=utc_now(),
        locked_at=utc_now(),
        locked_until=utc_now() + timedelta(minutes=5),
        heartbeat_at=utc_now(),
        lease_token="lease-1",
    )


def session_factory_for(job: Job) -> tuple[AsyncMock, dict[str, JobAttempt]]:
    session = AsyncMock()
    attempts: dict[str, JobAttempt] = {}

    def add(entity: object) -> None:
        if isinstance(entity, JobAttempt):
            entity.id = "attempt-1"
            attempts[entity.id] = entity

    async def get(model: type, entity_id: str, **_: object):
        if model is Job:
            return job
        if model is JobAttempt:
            return attempts.get(entity_id)
        return None

    session.add = MagicMock(side_effect=add)
    session.get.side_effect = get
    session.__aenter__.return_value = session
    session.__aexit__.return_value = False
    return session, attempts


class TestPayloadContract:
    def test_valid_payload_is_normalized(self) -> None:
        payload = validate_job_payload(
            "SCAN_DOCUMENT",
            {
                "tenant_id": "tenant-1",
                "matter_id": "matter-1",
                "document_id": "document-1",
                "revision_id": "revision-1",
                "s3_key": "quarantine/object.pdf",
                "expected_sha256": "a" * 64,
                "expected_size": 1024,
                "mime_type": "application/pdf",
            },
        )
        assert payload["revision_id"] == "revision-1"
        assert "type" not in payload

    @pytest.mark.parametrize(
        "payload",
        [
            {"tenant_id": "tenant-1", "matter_id": "matter-1"},
            {
                "tenant_id": "tenant-1",
                "matter_id": "matter-1",
                "document_id": "document-1",
                "revision_id": "revision-1",
                "s3_key": "object.pdf",
                "expected_sha256": "a" * 64,
                "expected_size": 1024,
                "mime_type": "application/pdf",
                "unexpected": True,
            },
        ],
    )
    def test_missing_or_unknown_fields_are_terminally_invalid(
        self, payload: dict
    ) -> None:
        with pytest.raises(ValidationError):
            validate_job_payload("SCAN_DOCUMENT", payload)


class TestRegistration:
    def test_default_batch_size_is_one(self) -> None:
        assert Worker().batch_size == 1

    @patch("apps.api.core.config.settings")
    def test_dummy_handler_is_blocked_in_secure_environments(
        self, mock_settings: MagicMock
    ) -> None:
        mock_settings.is_secure_environment = True
        worker = Worker()

        async def dummy_handler(payload: dict, session: object) -> None:
            return None

        with pytest.raises(RuntimeError, match="strictly prohibited"):
            worker.register("SCAN_DOCUMENT", dummy_handler)


class TestFailureSemantics:
    @pytest.mark.asyncio
    async def test_retryable_failure_requeues_with_backoff(self) -> None:
        job = make_job(attempts_made=1)
        attempt = JobAttempt(
            id="attempt-1",
            job_id=job.id,
            attempt_number=1,
            status="RUNNING",
            lease_token=job.lease_token,
        )
        session = AsyncMock()
        session.add = MagicMock()
        before = utc_now()

        await Worker()._fail_job(session, job, "temporary outage", attempt)

        assert job.status == JobStatus.PENDING
        assert job.retries == 2
        assert job.run_at >= before + timedelta(seconds=4)
        assert job.lease_token is None
        assert attempt.status == "FAILED"
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_terminal_failure_never_requeues(self) -> None:
        job = make_job(attempts_made=1)
        session = AsyncMock()
        session.add = MagicMock()

        await Worker()._fail_job(
            session,
            job,
            "invalid payload",
            retryable=False,
            error_class="ValidationError",
        )

        assert job.status == JobStatus.FAILED
        assert job.error_class == "ValidationError"
        assert job.lease_token is None

    @pytest.mark.asyncio
    async def test_retry_budget_exhaustion_goes_dead(self) -> None:
        job = make_job(attempts_made=3, max_retries=3)
        session = AsyncMock()
        session.add = MagicMock()
        await Worker()._fail_job(session, job, "still unavailable")
        assert job.status == JobStatus.DEAD
        assert job.retries == 0

    @pytest.mark.asyncio
    async def test_completion_requires_owned_running_lease(self) -> None:
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute.return_value = result

        completed = await Worker()._complete_job(session, "job-1", "stale-lease")

        assert completed is False


class TestProcessBoundary:
    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_invalid_payload_cannot_be_marked_succeeded(
        self, session_local: MagicMock
    ) -> None:
        job = make_job(job_type="SCAN_DOCUMENT", payload={"matter_id": "matter-1"})
        session, attempts = session_factory_for(job)
        session_local.return_value = session
        worker = Worker()
        completion = AsyncMock(return_value=True)
        worker._complete_job = completion

        await worker.process_job(job.id, "lease-1")

        completion.assert_not_awaited()
        assert job.status == JobStatus.FAILED
        assert job.error_class == "JobExecutionError"
        assert attempts["attempt-1"].status == "FAILED"
        assert get_tenant_id() is None

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_handler_exception_cannot_be_marked_succeeded(
        self, session_local: MagicMock
    ) -> None:
        job = make_job()
        session, _ = session_factory_for(job)
        session_local.return_value = session
        worker = Worker()

        async def fail_handler(payload: dict, db: object) -> None:
            raise RuntimeError("database unavailable")

        worker.register(job.type, fail_handler)
        completion = AsyncMock(return_value=True)
        worker._complete_job = completion

        await worker.process_job(job.id, "lease-1")

        completion.assert_not_awaited()
        assert job.status == JobStatus.PENDING
        assert job.attempts_made == 1
        assert get_tenant_id() is None

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_success_requires_handler_and_atomic_completion(
        self, session_local: MagicMock
    ) -> None:
        job = make_job()
        session, attempts = session_factory_for(job)
        session_local.return_value = session
        worker = Worker()
        handled = False

        async def successful_handler(payload: dict, db: object) -> None:
            nonlocal handled
            handled = True

        worker.register(job.type, successful_handler)
        worker._complete_job = AsyncMock(return_value=True)

        await worker.process_job(job.id, "lease-1")

        assert handled is True
        worker._complete_job.assert_awaited_once_with(session, job.id, "lease-1")
        assert attempts["attempt-1"].status == "SUCCEEDED"
        assert get_tenant_id() is None

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_lost_lease_records_attempt_without_failing_new_owner(
        self, session_local: MagicMock
    ) -> None:
        job = make_job()
        session, attempts = session_factory_for(job)
        session_local.return_value = session
        worker = Worker()

        async def successful_handler(payload: dict, db: object) -> None:
            return None

        worker.register(job.type, successful_handler)
        worker._complete_job = AsyncMock(return_value=False)
        worker._record_lost_lease = AsyncMock()
        fail_job = AsyncMock()
        worker._fail_job = fail_job

        await worker.process_job(job.id, "lease-1")

        fail_job.assert_not_awaited()
        worker._record_lost_lease.assert_awaited_once()
        assert attempts["attempt-1"].status == "RUNNING"
        assert get_tenant_id() is None

    @pytest.mark.asyncio
    @patch("apps.worker.core.queue.AsyncSessionLocal")
    async def test_expired_retry_budget_is_recovered_without_claim(
        self, session_local: MagicMock
    ) -> None:
        session = AsyncMock()
        empty = MagicMock()
        empty.scalars.return_value.all.return_value = []
        session.execute.side_effect = [MagicMock(), empty]
        session.__aenter__.return_value = session
        session.__aexit__.return_value = False
        session_local.return_value = session

        assert await Worker().process_batch() == 0
        assert session.execute.await_count == 2


def test_terminal_job_error_is_not_retryable() -> None:
    assert TerminalJobError.retryable is False
