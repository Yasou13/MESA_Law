from sqlalchemy import JSON, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .errors import ProblemException
from .models import AuditMixin, Base


class IdempotencyKey(Base, AuditMixin):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, default="in_progress")


async def check_idempotency(db: AsyncSession, key: str):
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
    result = await db.execute(stmt)
    idem = result.scalar_one_or_none()
    if idem:
        if idem.status == "in_progress":
            raise ProblemException(
                status=409, title="Conflict", detail="Request already in progress"
            )
        return idem

    idem = IdempotencyKey(key=key, status="in_progress")
    db.add(idem)
    await db.commit()
    return None


async def complete_idempotency(
    db: AsyncSession, key: str, status_code: int, response_body: dict
):
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == key)
    result = await db.execute(stmt)
    idem = result.scalar_one()
    idem.status = "completed"
    idem.status_code = status_code
    idem.response_body = response_body
    await db.commit()
