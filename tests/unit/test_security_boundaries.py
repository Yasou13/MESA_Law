from unittest.mock import AsyncMock, MagicMock

import pytest
from apps.api.core.errors import ProblemException
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy
from apps.api.core.rls import get_tenant_id, reset_tenant_id, set_tenant_id
from apps.api.dependencies.auth import get_current_user
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.asyncio
async def test_firm_admin_does_not_bypass_matter_membership():
    context = RequestContext(
        tenant_id="firm-1",
        principal_id="admin-1",
        roles={"FIRM_ADMIN"},
    )
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(ProblemException) as exc_info:
        await MatterAccessPolicy.can_read(context, db, "matter-1")

    assert exc_info.value.status == 403


@pytest.mark.asyncio
async def test_matter_policy_rejects_missing_scope():
    context = RequestContext(
        tenant_id="firm-1",
        principal_id="user-1",
        roles={"ATTORNEY"},
    )

    with pytest.raises(ProblemException) as exc_info:
        await MatterAccessPolicy.can_read(context, MagicMock(), "")

    assert exc_info.value.status == 400


def test_tenant_context_is_restored_with_token():
    outer = set_tenant_id("firm-outer")
    inner = set_tenant_id("firm-inner")
    try:
        assert get_tenant_id() == "firm-inner"
        reset_tenant_id(inner)
        assert get_tenant_id() == "firm-outer"
    finally:
        reset_tenant_id(outer)


@pytest.mark.asyncio
async def test_developer_token_is_rejected_without_explicit_test_auth():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="dev-mock-token"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
