from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.core.models import Base, AuditMixin, TenantAwareMixin

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
    
    user = relationship("User")
    firm = relationship("Firm")

class Matter(Base, AuditMixin, TenantAwareMixin):
    __tablename__ = "matters"
    title: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open", nullable=False)
