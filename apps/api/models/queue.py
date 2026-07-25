from datetime import datetime

from apps.api.core.models import AuditMixin, Base
from apps.api.core.utils import utc_now
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Job(Base, AuditMixin):
    __tablename__ = "legal_jobs"
    
    type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, default="pending") # pending, processing, completed, failed, dead
    
    # Retry and Leasing
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    # Dead letter reason
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    
    attempts = relationship("JobAttempt", back_populates="job", cascade="all, delete-orphan")

class JobAttempt(Base, AuditMixin):
    __tablename__ = "legal_job_attempts"
    
    job_id: Mapped[str] = mapped_column(ForeignKey("legal_jobs.id"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False) # success, failed
    error_details: Mapped[str | None] = mapped_column(String, nullable=True)
    
    job = relationship("Job", back_populates="attempts")

class Outbox(Base, AuditMixin):
    __tablename__ = "legal_outbox"
    
    event_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String, index=True, default="pending") # pending, published
