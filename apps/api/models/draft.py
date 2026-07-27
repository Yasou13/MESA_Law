from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

class Draft(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "drafts"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False) # JSON or HTML content from Tiptap
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    
    etag: Mapped[str] = mapped_column(String, nullable=False, default="v1")
    # State tracking for export: draft, review, APPROVED_FOR_EXTERNAL_USE
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)

class DraftRevision(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "draft_revisions"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str] = mapped_column(String, nullable=True)

class DraftCitation(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "draft_citations"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    draft_revision_id: Mapped[str] = mapped_column(ForeignKey("draft_revisions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    document_id: Mapped[str] = mapped_column(String, nullable=True)
    document_revision_id: Mapped[str] = mapped_column(String, nullable=True)
    source_locator_id: Mapped[str] = mapped_column(String, nullable=True)
    
    citation_text: Mapped[str] = mapped_column(String, nullable=False)
    verification_state: Mapped[str] = mapped_column(String, default="unverified", nullable=False)
