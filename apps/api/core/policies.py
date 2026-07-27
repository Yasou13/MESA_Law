from typing import Set
from apps.api.core.models import RequestContext
from apps.api.core.errors import ProblemException

class MatterAccessPolicy:
    @staticmethod
    def can_read(context: RequestContext, matter_id: str):
        # Admin, Attorney, Paralegal, Read-only, Auditor can read
        allowed = {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL", "READ_ONLY", "AUDITOR"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to read matters.")

    @staticmethod
    def can_create(context: RequestContext):
        allowed = {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to create matters.")

class DocumentAccessPolicy:
    @staticmethod
    def can_upload(context: RequestContext, matter_id: str):
        allowed = {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to upload documents.")

class ReviewAccessPolicy:
    @staticmethod
    def can_approve(context: RequestContext, matter_id: str):
        allowed = {"FIRM_ADMIN", "ATTORNEY"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to approve AI reviews.")

class ExportAccessPolicy:
    @staticmethod
    def can_export(context: RequestContext):
        allowed = {"FIRM_ADMIN", "ATTORNEY"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to export drafts.")

class DraftAccessPolicy:
    @staticmethod
    def can_manage(context: RequestContext):
        allowed = {"FIRM_ADMIN", "ATTORNEY", "PARALEGAL"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to manage drafts.")

class DeadlineAccessPolicy:
    @staticmethod
    def can_manage(context: RequestContext):
        allowed = {"FIRM_ADMIN", "ATTORNEY"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have permission to manage deadlines.")

class SupportAccessPolicy:
    @staticmethod
    def can_access(context: RequestContext):
        allowed = {"SUPPORT_TEMPORARY"}
        if not context.roles.intersection(allowed):
            raise ProblemException(status=403, title="Forbidden", detail="You do not have support access permission.")
