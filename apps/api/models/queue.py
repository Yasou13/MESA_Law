import enum
from datetime import datetime

from apps.api.core.models import AuditMixin, Base
from apps.api.core.utils import utc_now
from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD = "DEAD"


class Job(Base, AuditMixin):
    __tablename__ = "legal_jobs"

    type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, length=20),
        index=True,
        default=JobStatus.PENDING,
        nullable=False,
    )
    tenant_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    matter_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    # Retry and Leasing
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    attempts_made: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lease_token: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)

    # Dead letter reason
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    error_class: Mapped[str | None] = mapped_column(String, nullable=True)

    attempts = relationship(
        "JobAttempt", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'DEAD')",
            name="ck_legal_jobs_status",
        ),
        Index(
            "uq_legal_jobs_idempotency",
            "tenant_id",
            "type",
            "idempotency_key",
            unique=True,
            postgresql_where=idempotency_key.is_not(None),
        ),
    )


class JobAttempt(Base, AuditMixin):
    __tablename__ = "legal_job_attempts"

    job_id: Mapped[str] = mapped_column(
        ForeignKey("legal_jobs.id"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_details: Mapped[str | None] = mapped_column(String, nullable=True)
    lease_token: Mapped[str | None] = mapped_column(String, nullable=True)

    job = relationship("Job", back_populates="attempts")


class Outbox(Base, AuditMixin):
    __tablename__ = "legal_outbox"

    event_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String, index=True, default="pending"
    )  # pending, published
