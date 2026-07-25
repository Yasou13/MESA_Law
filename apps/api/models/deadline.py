from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import ForeignKey, String, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column

class DeadlineRule(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "deadline_rules"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    trigger_event: Mapped[str] = mapped_column(String, nullable=False)
    offset_days: Mapped[int] = mapped_column(nullable=False)

class PotentialDeadline(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "potential_deadlines"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("deadline_rules.id"), nullable=False)
    calculated_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending_approval", nullable=False)
    
class ApprovedDeadline(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "approved_deadlines"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    potential_deadline_id: Mapped[str] = mapped_column(ForeignKey("potential_deadlines.id"), nullable=False)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
