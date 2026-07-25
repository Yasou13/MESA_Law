from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

class SourcePackage(Base, AuditMixin):
    __tablename__ = "source_packages"
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String, default="1.0.0", nullable=False)

class LegalResource(Base, AuditMixin):
    """A specific case, statute, or regulation from a source package."""
    __tablename__ = "legal_resources"
    source_package_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    citation: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
