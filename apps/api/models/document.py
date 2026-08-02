import enum
from datetime import datetime

from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
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

    matter_id: Mapped[str] = mapped_column(
        ForeignKey("matters.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    matter = relationship("Matter")
    revisions = relationship(
        "DocumentRevision",
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentRevision(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "document_revisions"

    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # A revision is provisional while its bytes live under quarantine_key. The
    # immutable s3_key is assigned only after validation and malware scanning.
    quarantine_key: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    s3_key: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    is_canonical: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    immutable_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    # Metadata for Chain of Custody
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)

    # Full Phase 4 Quarantine State Machine
    from sqlalchemy import Enum as SQLEnum

    scan_status: Mapped[DocumentState] = mapped_column(
        SQLEnum(DocumentState, native_enum=False, length=50),
        default=DocumentState.UPLOAD_INTENT_CREATED,
        nullable=False,
    )

    document = relationship("Document", back_populates="revisions")
