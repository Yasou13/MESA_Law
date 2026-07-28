from apps.api.models.audit import AuditEvent, Notification
from sqlalchemy.ext.asyncio import AsyncSession


async def log_audit_event(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    changes: dict = None
):
    event = AuditEvent(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes
    )
    session.add(event)
    await session.commit()

async def create_notification(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    title: str,
    message: str
):
    notification = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        message=message
    )
    session.add(notification)
    await session.commit()
