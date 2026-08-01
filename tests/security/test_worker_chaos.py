"""Worker recovery and failure-boundary security tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apps.api.core.rls import get_tenant_id
from apps.api.models.queue import JobStatus
from apps.worker.core.queue import Worker
from apps.worker.jobs import TerminalJobError
from apps.worker.test_worker import make_job, session_factory_for


@pytest.mark.asyncio
async def test_only_one_worker_can_complete_a_lease() -> None:
    session = AsyncMock()
    winner = MagicMock()
    winner.scalar_one_or_none.return_value = "job-1"
    loser = MagicMock()
    loser.scalar_one_or_none.return_value = None
    session.execute.side_effect = [winner, loser]
    worker = Worker()

    assert await worker._complete_job(session, "job-1", "lease-a") is True
    assert await worker._complete_job(session, "job-1", "lease-b") is False


@pytest.mark.asyncio
async def test_error_history_is_bounded_and_preserved() -> None:
    job = make_job(attempts_made=3, max_retries=3)
    session = AsyncMock()
    session.add = MagicMock()

    await Worker()._fail_job(session, job, "x" * 2500)

    assert job.status == JobStatus.DEAD
    assert job.error_message == "x" * 2000


@pytest.mark.asyncio
@patch("apps.worker.core.queue.AsyncSessionLocal")
async def test_terminal_handler_error_never_retries(
    session_local: MagicMock,
) -> None:
    job = make_job()
    session, _ = session_factory_for(job)
    session_local.return_value = session
    worker = Worker()

    async def poison_handler(payload: dict, db: object) -> None:
        raise TerminalJobError("corrupt input")

    worker.register(job.type, poison_handler)
    worker._complete_job = AsyncMock(return_value=True)

    await worker.process_job(job.id, "lease-1")

    worker._complete_job.assert_not_awaited()
    assert job.status == JobStatus.FAILED
    assert "corrupt input" in (job.error_message or "")
    assert get_tenant_id() is None


@pytest.mark.asyncio
@patch("apps.worker.core.queue.AsyncSessionLocal")
async def test_retryable_crash_requeues_and_cleans_tenant_context(
    session_local: MagicMock,
) -> None:
    job = make_job()
    session, _ = session_factory_for(job)
    session_local.return_value = session
    worker = Worker()

    async def crashing_handler(payload: dict, db: object) -> None:
        raise RuntimeError("worker process crashed")

    worker.register(job.type, crashing_handler)
    worker._complete_job = AsyncMock(return_value=True)

    await worker.process_job(job.id, "lease-1")

    assert job.status == JobStatus.PENDING
    assert job.attempts_made == 1
    assert job.lease_token is None
    assert get_tenant_id() is None


@pytest.mark.asyncio
async def test_lost_lease_attempt_is_closed_without_touching_job() -> None:
    job = make_job()
    attempt = MagicMock()
    attempt.id = "attempt-1"
    attempt.lease_token = "lease-1"
    session = AsyncMock()

    await Worker()._record_lost_lease(session, attempt, "lease expired")

    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()
    assert job.status == JobStatus.RUNNING
