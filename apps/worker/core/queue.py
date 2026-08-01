import asyncio
import contextlib
import logging
import time
from collections.abc import Awaitable, Callable
from datetime import timedelta

from apps.api.core.database import AsyncSessionLocal
from apps.api.core.observability import get_meter, job_id_cv, tenant_id_cv
from apps.api.core.rls import reset_tenant_id, set_tenant_id
from apps.api.core.utils import generate_uuid, utc_now
from apps.api.models.queue import Job, JobAttempt, JobStatus
from apps.worker.jobs import JobExecutionError, LostLeaseError, validate_job_payload
from opentelemetry import trace
from pydantic import ValidationError
from sqlalchemy import or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("worker.queue")
HandlerFunc = Callable[[dict, AsyncSession], Awaitable[None]]


class Worker:
    def __init__(self, batch_size: int = 1, lease_minutes: int = 5):
        self.handlers: dict[str, HandlerFunc] = {}
        self._running = False
        self.batch_size = max(1, batch_size)
        self.lease_duration = timedelta(minutes=lease_minutes)

    def register(self, job_type: str, handler: HandlerFunc) -> None:
        if getattr(handler, "__name__", "") == "dummy_handler" or "dummy" in getattr(
            handler, "__name__", ""
        ):
            from apps.api.core.config import settings

            if settings.is_secure_environment:
                raise RuntimeError(
                    f"CRITICAL: No handler implemented for job type '{job_type}'. "
                    "Dummy handlers are strictly prohibited in production."
                )
        self.handlers[job_type] = handler

    async def start(self) -> None:
        self._running = True
        while self._running:
            processed = await self.process_batch()
            if processed == 0:
                await asyncio.sleep(1)

    def stop(self) -> None:
        self._running = False

    async def process_batch(self) -> int:
        now = utc_now()
        lease_token = generate_uuid()
        async with AsyncSessionLocal() as session:
            # A worker can die after recording its final allowed attempt. Such a
            # stale job must become terminal instead of being claimed forever.
            await session.execute(
                update(Job)
                .where(
                    Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
                    Job.attempts_made >= Job.max_retries,
                    or_(Job.locked_until.is_(None), Job.locked_until <= now),
                )
                .values(
                    status=JobStatus.DEAD,
                    error_class="RetryBudgetExhausted",
                    error_message="Retry budget exhausted before recovery claim",
                    locked_at=None,
                    locked_until=None,
                    heartbeat_at=None,
                    lease_token=None,
                    updated_at=now,
                )
            )
            eligible = (
                select(Job.id)
                .where(
                    Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
                    Job.attempts_made < Job.max_retries,
                    Job.run_at <= now,
                    or_(Job.locked_until.is_(None), Job.locked_until <= now),
                )
                .order_by(Job.run_at, Job.created_at)
                .limit(self.batch_size)
                .with_for_update(skip_locked=True)
            )
            job_ids = list((await session.execute(eligible)).scalars().all())
            if not job_ids:
                return 0

            claim = (
                update(Job)
                .where(
                    Job.id.in_(job_ids),
                    Job.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
                    Job.attempts_made < Job.max_retries,
                    or_(Job.locked_until.is_(None), Job.locked_until <= now),
                )
                .values(
                    status=JobStatus.RUNNING,
                    lease_token=lease_token,
                    locked_at=now,
                    heartbeat_at=now,
                    locked_until=now + self.lease_duration,
                    updated_at=now,
                )
                .returning(Job.id)
            )
            claimed_ids = list((await session.execute(claim)).scalars().all())
            await session.commit()

        for job_id in claimed_ids:
            await self.process_job(job_id, lease_token)
        return len(claimed_ids)

    async def _heartbeat_loop(self, job_id: str, lease_token: str) -> None:
        interval = max(1.0, self.lease_duration.total_seconds() / 3)
        while True:
            await asyncio.sleep(interval)
            now = utc_now()
            async with AsyncSessionLocal() as heartbeat_session:
                result = await heartbeat_session.execute(
                    update(Job)
                    .where(
                        Job.id == job_id,
                        Job.status == JobStatus.RUNNING,
                        Job.lease_token == lease_token,
                    )
                    .values(
                        heartbeat_at=now,
                        locked_until=now + self.lease_duration,
                        updated_at=now,
                    )
                    .returning(Job.id)
                )
                await heartbeat_session.commit()
                if result.scalar_one_or_none() is None:
                    raise LostLeaseError(f"Lease lost for job {job_id}")

    async def _complete_job(
        self, session: AsyncSession, job_id: str, lease_token: str
    ) -> bool:
        """Atomically complete a job only while this worker owns its lease."""
        completed_at = utc_now()
        result = await session.execute(
            update(Job)
            .where(
                Job.id == job_id,
                Job.status == JobStatus.RUNNING,
                Job.lease_token == lease_token,
            )
            .values(
                status=JobStatus.SUCCEEDED,
                locked_at=None,
                locked_until=None,
                heartbeat_at=None,
                lease_token=None,
                error_message=None,
                error_class=None,
                updated_at=completed_at,
            )
            .returning(Job.id)
        )
        return result.scalar_one_or_none() is not None

    async def _record_lost_lease(
        self, session: AsyncSession, attempt: JobAttempt, message: str
    ) -> None:
        await session.execute(
            update(JobAttempt)
            .where(
                JobAttempt.id == attempt.id,
                JobAttempt.lease_token == attempt.lease_token,
                JobAttempt.status == "RUNNING",
            )
            .values(
                status="LOST_LEASE",
                error_details=message[:2000],
                finished_at=utc_now(),
            )
        )
        await session.commit()

    async def process_job(
        self, job_id: str, expected_lease_token: str | None = None
    ) -> None:
        async with AsyncSessionLocal() as session:
            job = await session.get(Job, job_id)
            if job is None:
                return

            lease_token = expected_lease_token or job.lease_token
            if lease_token is None:
                lease_token = generate_uuid()
                now = utc_now()
                job.status = JobStatus.RUNNING
                job.lease_token = lease_token
                job.locked_at = now
                job.heartbeat_at = now
                job.locked_until = now + self.lease_duration
                await session.commit()
            elif job.lease_token != lease_token or job.status != JobStatus.RUNNING:
                logger.warning(
                    "Skipping job %s because its lease is no longer owned", job_id
                )
                return

            job.attempts_made += 1
            job.retries = max(0, job.max_retries - job.attempts_made)
            attempt = JobAttempt(
                job_id=job.id,
                attempt_number=job.attempts_made,
                status="RUNNING",
                lease_token=lease_token,
            )
            session.add(attempt)
            await session.commit()

            duration_histogram = get_meter("mesa.worker").create_histogram(
                "job_processing_duration", description="Time spent processing a job"
            )
            tracer = trace.get_tracer(__name__)
            start_time = time.monotonic()
            job_token = job_id_cv.set(job.id)
            observable_tenant_token = tenant_id_cv.set(job.tenant_id)
            tenant_token = set_tenant_id(job.tenant_id)
            heartbeat = asyncio.create_task(
                self._heartbeat_loop(job.id, lease_token),
                name=f"heartbeat:{job.id}",
            )

            try:
                await session.execute(
                    text("SELECT set_config('app.current_tenant', :tenant, true)"),
                    {"tenant": str(job.tenant_id)},
                )
                handler = self.handlers.get(job.type)
                if handler is None:
                    raise JobExecutionError(
                        f"FAILED_UNSUPPORTED_JOB_TYPE: No handler registered for {job.type}"
                    )
                try:
                    payload = validate_job_payload(
                        job.type,
                        {
                            **dict(job.payload),
                            "tenant_id": job.tenant_id,
                            "matter_id": job.matter_id
                            or dict(job.payload).get("matter_id"),
                        },
                    )
                except ValidationError as exc:
                    raise JobExecutionError(f"INVALID_JOB_PAYLOAD: {exc}") from exc

                with tracer.start_as_current_span(f"process_job_{job.type}") as span:
                    span.set_attribute("job.id", job.id)
                    span.set_attribute("job.type", job.type)
                    span.set_attribute("tenant.id", job.tenant_id)
                    await handler(payload, session)

                completed_at = utc_now()
                if not await self._complete_job(session, job.id, lease_token):
                    raise LostLeaseError(
                        f"Cannot complete job {job.id}; lease was lost"
                    )
                attempt.status = "SUCCEEDED"
                attempt.finished_at = completed_at
                await session.commit()
                duration_histogram.record(
                    time.monotonic() - start_time,
                    {"job.type": job.type, "status": "success"},
                )
            except Exception as exc:  # noqa: BLE001 - boundary classifies all handlers
                duration_histogram.record(
                    time.monotonic() - start_time,
                    {"job.type": job.type, "status": "failed"},
                )
                await session.rollback()
                if isinstance(exc, LostLeaseError):
                    logger.error("Job %s lost its lease: %s", job_id, exc)
                    await self._record_lost_lease(session, attempt, str(exc))
                    return

                owned_job = await session.get(Job, job_id, populate_existing=True)
                stored_attempt = await session.get(
                    JobAttempt, attempt.id, populate_existing=True
                )
                if (
                    owned_job
                    and owned_job.status == JobStatus.RUNNING
                    and owned_job.lease_token == lease_token
                ):
                    retryable = not isinstance(exc, JobExecutionError) or exc.retryable
                    await self._fail_job(
                        session,
                        owned_job,
                        str(exc),
                        stored_attempt,
                        retryable=retryable,
                        error_class=type(exc).__name__,
                    )
                else:
                    logger.error(
                        "Job %s failed after its lease was lost: %s", job_id, exc
                    )
            finally:
                heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError, LostLeaseError):
                    await heartbeat
                reset_tenant_id(tenant_token)
                tenant_id_cv.reset(observable_tenant_token)
                job_id_cv.reset(job_token)

    async def _fail_job(
        self,
        session: AsyncSession,
        job: Job,
        error_msg: str,
        attempt: JobAttempt | None = None,
        *,
        retryable: bool = True,
        error_class: str = "JobHandlerError",
    ) -> None:
        message = error_msg[:2000]
        job.error_message = message
        job.error_class = error_class
        if attempt is not None:
            attempt.status = "FAILED"
            attempt.error_details = message
            attempt.finished_at = utc_now()

        exhausted = job.attempts_made >= job.max_retries
        if not retryable:
            job.status = JobStatus.FAILED
        elif exhausted:
            job.status = JobStatus.DEAD
        else:
            job.status = JobStatus.PENDING
            backoff_seconds = min(300, 5 * (2 ** max(0, job.attempts_made - 1)))
            job.run_at = utc_now() + timedelta(seconds=backoff_seconds)

        job.retries = max(0, job.max_retries - job.attempts_made)
        job.locked_at = None
        job.locked_until = None
        job.heartbeat_at = None
        job.lease_token = None
        if job.status in {JobStatus.FAILED, JobStatus.DEAD}:
            await self._mark_terminal_document_state(session, job, message)
        session.add(job)
        if attempt is not None:
            session.add(attempt)
        await session.commit()

    async def _mark_terminal_document_state(
        self, session: AsyncSession, job: Job, message: str
    ) -> None:
        if job.type not in {
            "SCAN_DOCUMENT",
            "PARSE_DOCUMENT",
            "OCR_DOCUMENT",
            "EXTRACT_LEGAL_DATA",
            "EXTRACT_LEGAL_FACTS",
        }:
            return
        revision_id = dict(job.payload).get("revision_id")
        if revision_id is None and job.type.startswith("EXTRACT_"):
            from apps.api.models.parser import ParsedDocument

            parsed_id = dict(job.payload).get("parsed_document_id")
            parsed = await session.get(ParsedDocument, parsed_id) if parsed_id else None
            revision_id = parsed.revision_id if parsed else None
        if revision_id is None:
            return

        from apps.api.models.document import DocumentRevision, DocumentState

        revision = await session.get(DocumentRevision, revision_id)
        if revision is None:
            return
        revision.scan_status = (
            DocumentState.MANUAL_REVIEW_REQUIRED
            if job.type == "OCR_DOCUMENT"
            else DocumentState.FAILED
        )
        revision.failure_reason = message
