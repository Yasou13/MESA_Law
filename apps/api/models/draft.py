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
