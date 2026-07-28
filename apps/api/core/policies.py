
from apps.api.core.errors import ProblemException
from apps.api.core.models import RequestContext
from apps.api.models.domain import Role


class BasePolicy:
    @staticmethod
    def _enforce(context: RequestContext, allowed: set[Role], action: str):
        # Context roles might be strings if loaded from JWT, convert them safely
        # or compare with string values of Role.
        user_roles = {r for r in context.roles}
        allowed_str = {r.value for r in allowed}
        if not user_roles.intersection(allowed_str):
            raise ProblemException(status=403, title="Forbidden", detail=f"You do not have permission to {action}.")

class MatterAccessPolicy:
    @staticmethod
    def can_read(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL, Role.READ_ONLY, Role.AUDITOR}, "read matters")

    @staticmethod
    def can_create(context: RequestContext):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "create matters")

    @staticmethod
    def can_manage_members(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "manage matter members")

    @staticmethod
    def can_close(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "close matters")

class DocumentAccessPolicy:
    @staticmethod
    def can_upload(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL}, "upload documents")

    @staticmethod
    def can_read(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY, Role.PARALEGAL, Role.READ_ONLY, Role.AUDITOR}, "read documents")

class ReviewAccessPolicy:
    @staticmethod
    def can_approve(context: RequestContext, matter_id: str = None):
        BasePolicy._enforce(context, {Role.FIRM_ADMIN, Role.ATTORNEY}, "approve or reject AI reviews")

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
