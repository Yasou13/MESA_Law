
import pytest
from apps.api.core.database import AsyncSessionLocal
from apps.api.models.queue import Job, JobAttempt
from apps.worker.core.queue import Worker
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Dummy idempotent handler
executions = 0
async def sample_handler(payload: dict, session: AsyncSession):
    global executions
    executions += 1
    if payload.get("should_fail"):
        raise ValueError("Simulated failure")

@pytest.mark.asyncio
async def test_worker_processing():
    global executions
    executions = 0
    worker = Worker(lease_minutes=1)
    worker.register("test_job", sample_handler)
    
    # Insert job
    async with AsyncSessionLocal() as session:
        job = Job(type="test_job", payload={"hello": "world"})
        session.add(job)
        await session.commit()
        job_id = job.id
        
    # Process batch
    processed = await worker.process_batch()
    assert processed == 1
    assert executions == 1
    
    # Verify job status
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        assert job.status == "completed"
        assert job.locked_until is None
        
        # Verify attempt
        stmt = select(func.count(JobAttempt.id)).where(JobAttempt.job_id == job_id)
        attempts_count = await session.scalar(stmt)
        assert attempts_count == 1

@pytest.mark.asyncio
async def test_worker_failure_and_retry():
    worker = Worker(lease_minutes=1)
    worker.register("fail_job", sample_handler)
    
    async with AsyncSessionLocal() as session:
        job = Job(type="fail_job", payload={"should_fail": True}, max_retries=2)
        session.add(job)
        await session.commit()
        job_id = job.id
        
    # Attempt 1
    await worker.process_batch()
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        assert job.status == "pending"
        assert job.retries == 1
        assert "Simulated failure" in job.error_message
        
    # We must reset run_at to simulate time passing for backoff
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        from apps.api.core.utils import utc_now
        job.run_at = utc_now()
        await session.commit()
        
    # Attempt 2
    await worker.process_batch()
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        assert job.status == "dead"
        assert job.retries == 2
        
@pytest.mark.asyncio
async def test_duplicate_delivery_idempotency():
    # If a worker dies and the lease expires, another worker picks it up.
    # The business logic handler must be idempotent.
    # We simulate this by taking a job, setting locked_until to past.
    worker = Worker(lease_minutes=1)
    worker.register("test_idempotent", sample_handler)
    
    async with AsyncSessionLocal() as session:
        job = Job(type="test_idempotent", payload={})
        session.add(job)
        await session.commit()
        job_id = job.id
        
    # Worker 1 locks but dies before processing completes
    async with AsyncSessionLocal() as session:
        from datetime import timedelta

        from apps.api.core.utils import utc_now
        # Simulate lock expired
        job = await session.get(Job, job_id)
        job.status = "processing"
        job.locked_until = utc_now() - timedelta(minutes=5)
        await session.commit()
        
    # Worker 2 picks it up (lease expired)
    await worker.process_batch()
    
    async with AsyncSessionLocal() as session:
        job = await session.get(Job, job_id)
        assert job.status == "completed"
