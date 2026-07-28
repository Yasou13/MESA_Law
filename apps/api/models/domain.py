import enum

from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Role(str, enum.Enum):
    FIRM_ADMIN = "FIRM_ADMIN"
    ATTORNEY = "ATTORNEY"
    PARALEGAL = "PARALEGAL"
    READ_ONLY = "READ_ONLY"
    AUDITOR = "AUDITOR"
    SUPPORT_TEMPORARY = "SUPPORT_TEMPORARY"

class Firm(Base, AuditMixin):
    __tablename__ = "firms"
    name: Mapped[str] = mapped_column(String, nullable=False)

class User(Base, AuditMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    
    from datetime import datetime
    from sqlalchemy import DateTime
    is_support_access_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    support_access_granted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Membership(Base, AuditMixin):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    role: Mapped[Role] = mapped_column(SQLEnum(Role, native_enum=False, length=50), default=Role.READ_ONLY, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    user = relationship("User")
    firm = relationship("Firm")

class Matter(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matters"
    title: Mapped[str] = mapped_column(String, nullable=False)
    internal_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)
    client_name: Mapped[str | None] = mapped_column(String, nullable=True)
    responsible_attorney_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String, nullable=True)
    case_type: Mapped[str | None] = mapped_column(String, nullable=True)
    confidentiality_level: Mapped[str] = mapped_column(String, default="standard", nullable=False)
    ai_processing_policy: Mapped[str] = mapped_column(String, default="standard", nullable=False)
    
    from datetime import datetime
    from sqlalchemy import DateTime
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class MatterMember(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matter_members"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    access_scope: Mapped[str] = mapped_column(String, default="read", nullable=False) # read, write, admin

class MatterParty(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matter_parties"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False) # e.g. PLAINTIFF, DEFENDANT
    type: Mapped[str] = mapped_column(String, nullable=False) # e.g. PERSON, ORGANIZATION
    
class Claim(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "claims"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    claimant_party_id: Mapped[str] = mapped_column(ForeignKey("matter_parties.id"), nullable=False)
    defendant_party_id: Mapped[str] = mapped_column(ForeignKey("matter_parties.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    # AI models create claims in 'suggested' state; humans move them to 'approved'.
    review_status: Mapped[str] = mapped_column(String, default="approved", nullable=False)

class EvidenceItem(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "evidence_items"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=True) # Source document
    description: Mapped[str] = mapped_column(String, nullable=False)
    review_status: Mapped[str] = mapped_column(String, default="approved", nullable=False)

class LegalAssertion(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "legal_assertions"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=True)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_items.id", ondelete="CASCADE"), index=True, nullable=True)
    legal_source_id: Mapped[str | None] = mapped_column(ForeignKey("legal_sources.id", ondelete="SET NULL"), index=True, nullable=True)
    assertion_text: Mapped[str] = mapped_column(String, nullable=False)
    source_locator_id: Mapped[str | None] = mapped_column(ForeignKey("source_locators.id", ondelete="SET NULL"), index=True, nullable=True)
    review_status: Mapped[str] = mapped_column(String, default="approved", nullable=False)

class MatterEvent(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matter_events"
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=False)
    
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    
    from datetime import datetime

    from sqlalchemy import DateTime
    
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_precision: Mapped[str] = mapped_column(String, default="day", nullable=False) # day, month, year
    
    source_locator_id: Mapped[str | None] = mapped_column(ForeignKey("source_locators.id", ondelete="SET NULL"), index=True, nullable=True)
    review_state: Mapped[str] = mapped_column(String, default="approved", nullable=False)
    
    # Keeping old fields for backwards compatibility with worker scripts if needed
    source_type: Mapped[str] = mapped_column(String, default="document", nullable=False)
    confidence: Mapped[str] = mapped_column(String, default="high")

class ClaimEvidenceLink(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "claim_evidence_links"
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True, nullable=False)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence_items.id", ondelete="CASCADE"), index=True, nullable=False)
    support_type: Mapped[str] = mapped_column(String, default="supports") # supports, refutes, partial

class SourceLocator(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "source_locators"
    matter_id: Mapped[str | None] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), index=True, nullable=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    document_revision_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    parsed_document_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    parsed_page_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    
    page_number: Mapped[int] = mapped_column(nullable=False)
    paragraph_index: Mapped[int | None] = mapped_column(nullable=True)
    block_index: Mapped[int | None] = mapped_column(nullable=True)
    
    character_start: Mapped[int | None] = mapped_column(nullable=True)
    character_end: Mapped[int | None] = mapped_column(nullable=True)
    
    bbox_x0: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_y0: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_x1: Mapped[float | None] = mapped_column(Float, nullable=True)
    bbox_y1: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    text_snippet: Mapped[str | None] = mapped_column(String, nullable=True)
    text_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    
    parser_version: Mapped[str | None] = mapped_column(String, nullable=True)
    ocr_version: Mapped[str | None] = mapped_column(String, nullable=True)
