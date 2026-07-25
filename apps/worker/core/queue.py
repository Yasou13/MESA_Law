import asyncio
from datetime import timedelta
from typing import Callable, Awaitable, Dict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.models.queue import Job, JobAttempt
from apps.api.core.database import AsyncSessionLocal
from apps.api.core.utils import utc_now

HandlerFunc = Callable[[dict, AsyncSession], Awaitable[None]]

class Worker:
    def __init__(self, batch_size=10, lease_minutes=5):
        self.handlers: Dict[str, HandlerFunc] = {}
        self._running = False
        self.batch_size = batch_size
        self.lease_duration = timedelta(minutes=lease_minutes)
    
    def register(self, job_type: str, handler: HandlerFunc):
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
                retries=Job.retries + 1,
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
                await self._fail_job(session, job, f"No handler registered for {job.type}")
                return
                
            attempt = JobAttempt(
                job_id=job.id,
                attempt_number=job.retries,
                status="processing"
            )
            session.add(attempt)
            await session.commit()
            
            try:
                await handler(job.payload, session)
                
                # Refresh job since handler might have modified session state
                job = await session.get(Job, job_id)
                job.status = "completed"
                job.locked_until = None
                job.error_message = None
                attempt.status = "success"
                attempt.finished_at = utc_now()
                await session.commit()
                
            except Exception as e:
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
            
        if job.retries >= job.max_retries:
            job.status = "dead"
            job.locked_until = None
        else:
            job.status = "pending"
            job.locked_until = None
            job.run_at = utc_now() + timedelta(seconds=(2 ** job.retries) * 5)
            
        session.add(job)
        if attempt:
            session.add(attempt)
        await session.commit()
