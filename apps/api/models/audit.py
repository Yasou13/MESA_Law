from datetime import datetime

from apps.api.core.models import AuditMixin, Base
from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column


class AuditEvent(Base, AuditMixin):
    __tablename__ = "audit_events"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    changes: Mapped[dict] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

class Notification(Base, AuditMixin):
    __tablename__ = "notifications"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    
    # Phase 12 Categories: processing_failed, review_pending, deadline_approaching, source_stale, export_completed, support_access
    category: Mapped[str] = mapped_column(String, nullable=False, default="general")
    
    # Phase 12 Statuses: CREATED, DELIVERED, READ, ACKNOWLEDGED, ESCALATED, RESOLVED
    status: Mapped[str] = mapped_column(String, default="CREATED", nullable=False)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
