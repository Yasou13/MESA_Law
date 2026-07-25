from apps.api.core.models import AuditMixin, Base, TenantAwareMixin
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Firm(Base, AuditMixin):
    __tablename__ = "firms"
    name: Mapped[str] = mapped_column(String, nullable=False)

class User(Base, AuditMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    keycloak_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)

class Membership(Base, AuditMixin):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    firm_id: Mapped[str] = mapped_column(ForeignKey("firms.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    user = relationship("User")
    firm = relationship("Firm")

class Matter(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matters"
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)

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
    assertion_text: Mapped[str] = mapped_column(String, nullable=False)
    source_locator: Mapped[str] = mapped_column(String, nullable=True) # JSON dump of SourceLocator
    review_status: Mapped[str] = mapped_column(String, default="approved", nullable=False)
