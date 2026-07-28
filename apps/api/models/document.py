import enum

from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class DocumentState(str, enum.Enum):
    UPLOAD_INTENT_CREATED = "UPLOAD_INTENT_CREATED"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    VERIFYING = "VERIFYING"
    QUARANTINED = "QUARANTINED"
    SCANNING = "SCANNING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    PARSING = "PARSING"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_RUNNING = "OCR_RUNNING"
    PARSED = "PARSED"
    EXTRACTION_PENDING = "EXTRACTION_PENDING"
    READY = "READY"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

class Document(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "documents"
    
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    matter = relationship("Matter")
    revisions = relationship("DocumentRevision", back_populates="document", cascade="all, delete-orphan")

class DocumentRevision(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "document_revisions"
    
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Immutable storage key in S3 (e.g., {tenant_id}/{matter_id}/{uuid}.pdf)
    s3_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    # Metadata for Chain of Custody
    file_hash: Mapped[str | None] = mapped_column(String, nullable=True) # SHA-256 (set after upload)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    
    # Full Phase 4 Quarantine State Machine
    scan_status: Mapped[str] = mapped_column(String, default=DocumentState.UPLOAD_INTENT_CREATED.value, nullable=False) 
    
    document = relationship("Document", back_populates="revisions")
