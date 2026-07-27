from datetime import datetime

from apps.api.core.models import AuditMixin, Base
from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class ExtractionSuggestion(Base, AuditMixin):
    __tablename__ = "extraction_suggestions"
    
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("firms.id"), index=True, nullable=False)
    matter_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    document_revision_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_locator_id: Mapped[str] = mapped_column(String, nullable=True)
    
    suggestion_type: Mapped[str] = mapped_column(String, index=True, nullable=False) # e.g. CLAIM_SUGGESTION
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    extractor_name: Mapped[str] = mapped_column(String, nullable=False)
    extractor_version: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    parser_version: Mapped[str] = mapped_column(String, nullable=False)
    confidence_category: Mapped[str] = mapped_column(String, default="high")
    
    review_state: Mapped[str] = mapped_column(String, default="pending") # pending -> approved / rejected
    idempotency_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

class ReviewItem(Base, AuditMixin):
    __tablename__ = "review_items"
    
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("firms.id"), index=True, nullable=False)
    matter_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    # What are we reviewing? (e.g. 'document_extraction', 'timeline_event', 'claim')
    entity_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    
    # Optional link back to the raw suggestion
    suggestion_id: Mapped[str | None] = mapped_column(ForeignKey("extraction_suggestions.id"), nullable=True)
    
    # Original AI proposed content
    proposed_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # pending, approved, rejected, corrected
    status: Mapped[str] = mapped_column(String, index=True, default="pending")
    
    # Solo mode / Policy Engine fields
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
