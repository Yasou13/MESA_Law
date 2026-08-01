from datetime import datetime

from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


class MesaScopeBinding(Base, AuditMixin, TenantAwareMixin):
    """Stable Law-to-MESA v4 catalog mapping for one matter."""

    __tablename__ = "mesa_scope_bindings"

    matter_id: Mapped[str] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mesa_tenant_id: Mapped[str] = mapped_column(String, nullable=False)
    workspace_id: Mapped[str] = mapped_column(String, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    provisioning_status: Mapped[str] = mapped_column(
        String, nullable=False, default="PENDING"
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "matter_id", name="uq_mesa_binding_matter"),
        UniqueConstraint("tenant_id", "dataset_id", name="uq_mesa_binding_dataset"),
    )


class MesaSyncRecord(Base, AuditMixin, TenantAwareMixin):
    """Durable admission and mutation state for a MESA v4 write."""

    __tablename__ = "mesa_sync_records"

    matter_id: Mapped[str] = mapped_column(
        ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    binding_id: Mapped[str] = mapped_column(
        ForeignKey("mesa_scope_bindings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_locator_id: Mapped[str | None] = mapped_column(
        ForeignKey("source_locators.id", ondelete="SET NULL"), nullable=True
    )
    assertion_id: Mapped[str | None] = mapped_column(
        ForeignKey("legal_assertions.id", ondelete="SET NULL"), nullable=True
    )
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    mutation_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    candidate_id: Mapped[str | None] = mapped_column(String, nullable=True)
    pipeline_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String, nullable=True)
    last_polled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "idempotency_key", name="uq_mesa_sync_idempotency"
        ),
    )
