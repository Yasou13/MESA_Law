import enum

from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import JSON, Boolean, Date, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column


class DeadlineState(str, enum.Enum):
    POTENTIAL_DEADLINE = "POTENTIAL_DEADLINE"
    RULE_MATCHED = "RULE_MATCHED"
    CALCULATED = "CALCULATED"
    ATTORNEY_VERIFIED = "ATTORNEY_VERIFIED"
    SCHEDULED = "SCHEDULED"
    REJECTED = "REJECTED"

class DeadlineRulePack(Base, AuditMixin):
    __tablename__ = "deadline_rule_packs"
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

class HolidayCalendar(Base, AuditMixin):
    __tablename__ = "holiday_calendars"
    version: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    country_code: Mapped[str] = mapped_column(String, default="TR", nullable=False)
    # Could store actual dates as JSON or have a separate table
    dates: Mapped[dict] = mapped_column(JSON, nullable=False, default={})

class DeadlineRule(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "deadline_rules"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    
    rule_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    jurisdiction: Mapped[str] = mapped_column(String, nullable=True)
    procedure_type: Mapped[str] = mapped_column(String, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    
    duration: Mapped[int] = mapped_column(nullable=False)
    duration_unit: Mapped[str] = mapped_column(String, default="days", nullable=False) # days, weeks, months
    calculation_method: Mapped[str] = mapped_column(String, default="calendar_days", nullable=False) # calendar_days, business_days
    
    from datetime import datetime

    from sqlalchemy import DateTime
    
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    legal_source_id: Mapped[str] = mapped_column(ForeignKey("legal_sources.id"), nullable=True)
    holiday_calendar_version: Mapped[str] = mapped_column(String, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String, nullable=True)
    rule_pack_version: Mapped[str] = mapped_column(String, nullable=True)

class DeadlineCandidate(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "deadline_candidates"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rule_id: Mapped[str] = mapped_column(ForeignKey("deadline_rules.id"), nullable=False)
    
    trigger_event: Mapped[str | None] = mapped_column(String, nullable=True)
    trigger_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    calculation_trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    calculated_date: Mapped[Date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    
    # POTENTIAL_DEADLINE, RULE_MATCHED, CALCULATED, ATTORNEY_VERIFIED, SCHEDULED, REJECTED
    status: Mapped[DeadlineState] = mapped_column(SQLEnum(DeadlineState, name="deadline_state", create_type=False), default=DeadlineState.POTENTIAL_DEADLINE, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="Europe/Istanbul", nullable=False)
    
class ApprovedDeadline(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "approved_deadlines"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    
    deadline_candidate_id: Mapped[str] = mapped_column(ForeignKey("deadline_candidates.id"), nullable=False)
    
    due_date: Mapped[Date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String, default="Europe/Istanbul", nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
