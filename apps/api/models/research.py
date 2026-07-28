from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
import enum
from sqlalchemy import Enum as SQLEnum

class LegalSourceStatus(str, enum.Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    SYNC_FAILED = "SYNC_FAILED"
    LICENSE_RESTRICTED = "LICENSE_RESTRICTED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"

class SourcePackage(Base, AuditMixin):
    __tablename__ = "source_packages"
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String, default="1.0.0", nullable=False)

class LegalSource(Base, AuditMixin):
    """A specific case, statute, or regulation from a source package."""
    __tablename__ = "legal_sources"
    source_package_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    citation: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    source_type: Mapped[str] = mapped_column(String, nullable=False) # e.g. case_law, legislation
    jurisdiction: Mapped[str] = mapped_column(String, nullable=True)
    court: Mapped[str] = mapped_column(String, nullable=True)
    chamber: Mapped[str] = mapped_column(String, nullable=True)
    decision_number: Mapped[str] = mapped_column(String, nullable=True)
    
    from sqlalchemy import DateTime
    from datetime import datetime
    
    decision_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # CURRENT, STALE, SYNC_FAILED, LICENSE_RESTRICTED, SOURCE_UNAVAILABLE
    status: Mapped[LegalSourceStatus] = mapped_column(SQLEnum(LegalSourceStatus, name="legal_source_status", create_type=False), default=LegalSourceStatus.CURRENT, nullable=False)
    license_type: Mapped[str] = mapped_column(String, nullable=True)
    snapshot_id: Mapped[str] = mapped_column(String, nullable=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=True)
