from datetime import datetime

from apps.api.core.models import AuditMixin, Base
from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class ReviewQueue(Base, AuditMixin):
    __tablename__ = "legal_review_queue"
    
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("firms.id"), index=True, nullable=False)
    matter_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    # What are we reviewing? (e.g. 'document_extraction', 'timeline_event', 'claim')
    entity_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    # Original AI proposed content
    proposed_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # pending, approved, rejected, corrected
    status: Mapped[str] = mapped_column(String, index=True, default="pending")
    
    # Solo mode / Policy Engine fields
    # If the user is solo, external_use might be delayed (cooling-off)
    external_use_ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Who took action and when
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # If corrected, what is the new content?
    corrected_content: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class AuditLog(Base, AuditMixin):
    """Immutable audit trail for all legal state changes."""
    __tablename__ = "legal_audit_logs"
    
    tenant_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    matter_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    action: Mapped[str] = mapped_column(String, nullable=False) # e.g. 'APPROVE_CLAIM', 'REJECT_EVENT'
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    
    # Changes (before/after) or just the action payload
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
