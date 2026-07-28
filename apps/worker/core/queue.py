import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta

from apps.api.core.database import AsyncSessionLocal
from apps.api.core.utils import utc_now
from apps.api.models.queue import Job, JobAttempt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

HandlerFunc = Callable[[dict, AsyncSession], Awaitable[None]]

class Worker:
    def __init__(self, batch_size=10, lease_minutes=5):
        self.handlers: dict[str, HandlerFunc] = {}
        self._running = False
        self.batch_size = batch_size
        self.lease_duration = timedelta(minutes=lease_minutes)
    
    def register(self, job_type: str, handler: HandlerFunc):
        if getattr(handler, "__name__", "") == "dummy_handler" or "dummy" in getattr(handler, "__name__", ""):
            from apps.api.core.config import settings
            if settings.is_secure_environment:
                raise RuntimeError(f"CRITICAL: No handler implemented for job type '{job_type}'. Dummy handlers are strictly prohibited in production.")
        self.handlers[job_type] = handler
        
    async def start(self):
        self._running = True
        while self._running:
            processed = await self.process_batch()
            if processed == 0:
                await asyncio.sleep(1)
                
    def stop(self):
        self._running = False
        
    async def process_batch(self) -> int:
        processed_count = 0
        async with AsyncSessionLocal() as session:
            now = utc_now()
            
            stmt = select(Job.id).where(
                Job.status.in_(["pending", "processing"]),
                Job.run_at <= now,
                (Job.locked_until.is_(None)) | (Job.locked_until <= now)
            ).order_by(Job.run_at).limit(self.batch_size).with_for_update(skip_locked=True)
            
            result = await session.execute(stmt)
            job_ids = result.scalars().all()
            
            if not job_ids:
                return 0
                
            locked_until = now + self.lease_duration
            lock_stmt = update(Job).where(Job.id.in_(job_ids)).values(
                status="processing",
                locked_until=locked_until,
                updated_at=now
            ).returning(Job)
            
            jobs = (await session.execute(lock_stmt)).scalars().all()
            await session.commit()
            
            for job in jobs:
                await self.process_job(job.id)
                processed_count += 1
                
        return processed_count
        
    async def process_job(self, job_id: str):
        async with AsyncSessionLocal() as session:
            job = await session.get(Job, job_id)
            if not job:
                return
                
            handler = self.handlers.get(job.type)
            if not handler:
                await self._fail_job(session, job, f"FAILED_UNSUPPORTED_JOB_TYPE: No handler registered for {job.type}")
                return
                
            attempt = JobAttempt(
                job_id=job.id,
                attempt_number=job.retries,
                status="processing"
            )
            session.add(attempt)
            await session.commit()
            
            import time

            from apps.api.core.observability import get_meter, job_id_cv, tenant_id_cv
            from opentelemetry import trace
            
            meter = get_meter("mesa.worker")
            duration_histogram = meter.create_histogram("job_processing_duration", description="Time spent processing a job")
            
            job_id_cv.set(job.id)
            tenant_id_cv.set(job.payload.get("tenant_id"))
            
            tracer = trace.get_tracer(__name__)
            start_time = time.time()
            
            try:
                with tracer.start_as_current_span(f"process_job_{job.type}") as span:
                    span.set_attribute("job.id", job.id)
                    span.set_attribute("job.type", job.type)
                    if "tenant_id" in job.payload:
                        span.set_attribute("tenant.id", job.payload["tenant_id"])
                        
                    await handler(job.payload, session)
                    
                    # Refresh job since handler might have modified session state
                    job = await session.get(Job, job_id)
                    job.status = "completed"
                    job.locked_until = None
                    job.error_message = None
                    attempt.status = "success"
                    attempt.finished_at = utc_now()
                    await session.commit()
                    
                    duration_histogram.record(time.time() - start_time, {"job.type": job.type, "status": "success"})
                    
            except Exception as e:  # noqa: BLE001 — handlers may raise any exception
                duration_histogram.record(time.time() - start_time, {"job.type": job.type, "status": "failed"})
                
                await session.rollback()
                # Use a fresh session for failure update if needed, but since we rolled back, we can just use the same one
                # but we need to re-fetch the objects.
                job = await session.get(Job, job_id)
                attempt = await session.get(JobAttempt, attempt.id)
                await self._fail_job(session, job, str(e), attempt)

    async def _fail_job(self, session: AsyncSession, job: Job, error_msg: str, attempt: JobAttempt = None):
        job.error_message = error_msg
        if attempt:
            attempt.status = "failed"
            attempt.error_details = error_msg
            attempt.finished_at = utc_now()
            
        # Phase 16: Decrement retries (remaining attempts)
        job.retries = max(0, job.retries - 1)
            
        if job.retries == 0:
            job.status = "dead"
            job.locked_until = None
        else:
            job.status = "pending"
            job.locked_until = None
            # Exponential backoff based on attempts made (max_retries - retries)
            attempts_made = max(0, job.max_retries - job.retries)
            job.run_at = utc_now() + timedelta(seconds=(2 ** attempts_made) * 5)
            
        session.add(job)
        if attempt:
            session.add(attempt)
        await session.commit()
