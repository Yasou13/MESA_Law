"""MVP contract tests for the deliberately disabled AI drafting surface."""

from unittest.mock import AsyncMock, patch

import pytest
from apps.api.core.models import RequestContext
from apps.api.routers.draft_studio import GenerateDraftRequest, generate_draft
from fastapi import HTTPException, Request


@pytest.mark.asyncio
async def test_ai_draft_generation_is_fail_closed_by_default() -> None:
    request = Request({"type": "http", "method": "POST", "headers": []})
    context = RequestContext(
        tenant_id="firm-1", principal_id="attorney-1", roles={"ATTORNEY"}
    )
    database = AsyncMock()

    with (
        patch("apps.api.routers.draft_studio.settings.drafting_ai_enabled", False),
        pytest.raises(HTTPException) as raised,
    ):
        await generate_draft(
            request=request,
            payload=GenerateDraftRequest(matter_id="matter-1"),
            context=context,
            db=database,
        )

    assert raised.value.status_code == 501
    assert raised.value.detail == "AI draft generation is disabled in the MVP"
    database.add.assert_not_called()
    database.commit.assert_not_awaited()
