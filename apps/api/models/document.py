from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Document(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "documents"
    
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    matter = relationship("Matter")
    revisions = relationship("DocumentRevision", back_populates="document", cascade="all, delete-orphan")

class DocumentRevision(Base, AuditMixin):
    __tablename__ = "document_revisions"
    
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Immutable storage key in S3 (e.g., {tenant_id}/{matter_id}/{uuid}.pdf)
    s3_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    # Metadata for Chain of Custody
    file_hash: Mapped[str | None] = mapped_column(String, nullable=True) # SHA-256 (set after upload)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    
    # Quarantine State Machine (uploading -> scanning -> clean | infected)
    scan_status: Mapped[str] = mapped_column(String, default="uploading", nullable=False) 
    
    document = relationship("Document", back_populates="revisions")
