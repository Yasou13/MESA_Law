from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from .utils import generate_uuid, utc_now


class Base(DeclarativeBase):
    pass

class AuditMixin:
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @declared_attr
    def __mapper_args__(cls):
        return {"version_id_col": cls.version_id, "version_id_generator": False}

class TenantAwareMixin:
    """Mixin to add tenant context and enable RLS."""
    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        # Late binding using declared_attr to avoid Circular Import issues with firms table
        from sqlalchemy import ForeignKey, String
        from sqlalchemy.orm import mapped_column
        return mapped_column(String, ForeignKey("firms.id"), index=True, nullable=False)

class RequestContext(BaseModel):
    tenant_id: str
    principal_id: str
    roles: set[str]
