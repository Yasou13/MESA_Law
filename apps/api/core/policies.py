
from apps.api.core.errors import ProblemException
from apps.api.core.models import RequestContext
from apps.api.models.domain import MatterMember, Role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BasePolicy:
    @staticmethod
    def _enforce(context: RequestContext, allowed: set[Role], action: str):
        # Context roles might be strings if loaded from JWT, convert them safely
        # or compare with string values of Role.
        user_roles = {r for r in context.roles}
        allowed_str = {r.value for r in allowed}
        if not user_roles.intersection(allowed_str):
            raise ProblemException(status=403, title="Forbidden", detail=f"You do not have permission to {action}.")
            
    @staticmethod
    async def _enforce_matter(context: RequestContext, db: AsyncSession, matter_id: str, required_scopes: list[str]):
        if not matter_id:
            return
        # Firm admins bypass matter-level membership checks
        user_roles = {r.value if hasattr(r, 'value') else r for r in context.roles}
        if Role.FIRM_ADMIN.value in user_roles:
            return
            
        res = await db.execute(select(MatterMember).where(
            MatterMember.matter_id == matter_id,
            MatterMember.user_id == context.principal_id,
            MatterMember.tenant_id == context.tenant_id
        ))
        member = res.scalars().first()
        if not member:
            raise ProblemException(status=403, title="Forbidden", detail="You are not a member of this matter.")
            
        if required_scopes and member.access_scope not in required_scopes:
            raise ProblemException(status=403, title="Forbidden", detail=f"Requires one of scopes: {required_scopes}")

class MatterAccessPolicy:
    @staticmethod
    async def can_read(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL, Role.READ_ONLY, Role.AUDITOR}, "read matters")
        await BasePolicy._enforce_matter(context, db, matter_id, ["read", "write", "admin"])

    @staticmethod
    async def can_create(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "create matters")

    @staticmethod
    async def can_manage_members(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "manage matter members")
        await BasePolicy._enforce_matter(context, db, matter_id, ["admin"])

    @staticmethod
    async def can_close(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "close matters")
        await BasePolicy._enforce_matter(context, db, matter_id, ["admin"])

class DocumentAccessPolicy:
    @staticmethod
    async def can_upload(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "upload documents")
        await BasePolicy._enforce_matter(context, db, matter_id, ["write", "admin"])

    @staticmethod
    async def can_read(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL, Role.READ_ONLY, Role.AUDITOR}, "read documents")
        await BasePolicy._enforce_matter(context, db, matter_id, ["read", "write", "admin"])

class ReviewAccessPolicy:
    @staticmethod
    async def can_approve(context: RequestContext, db: AsyncSession, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "approve or reject AI reviews")
        await BasePolicy._enforce_matter(context, db, matter_id, ["write", "admin"])

class ExportAccessPolicy:
    @staticmethod
    def can_export(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "export drafts")

class DraftAccessPolicy:
    @staticmethod
    def can_manage(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "create and update drafts")

    @staticmethod
    def can_approve_external(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "approve drafts for external use")

class DeadlineAccessPolicy:
    @staticmethod
    def can_manage(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "manage deadlines")

    @staticmethod
    def can_verify(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "verify and approve deadlines")

class AdminAccessPolicy:
    @staticmethod
    def can_manage_firm(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN}, "manage firm membership and billing")

    @staticmethod
    def can_audit(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.AUDITOR}, "access audit logs")

    @staticmethod
    def can_rebuild_mesa(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "rebuild MESA index")

class SupportAccessPolicy:
    @staticmethod
    def can_access(context: RequestContext):
        BasePolicy._enforce(context, {Role.SUPPORT_TEMPORARY}, "access via temporary support mode")
