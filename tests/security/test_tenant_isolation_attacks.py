import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest
from apps.api.core.errors import ProblemException
from apps.api.core.models import RequestContext
from apps.api.models.document import Document
from apps.api.models.draft import Draft
from apps.api.routers.documents import download_document
from apps.api.routers.draft_studio import get_draft
from apps.api.routers.matters import get_matter
from fastapi import HTTPException, Request


@pytest.fixture
def tenant_a_context_and_db():
    context = RequestContext(
        tenant_id="tenant_A", principal_id="user_A", roles={"FIRM_ADMIN"}
    )
    db = AsyncMock()
    denied_membership = MagicMock()
    denied_membership.scalars.return_value.first.return_value = None
    db.execute.return_value = denied_membership
    return context, db


def request_for(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
        }
    )


@pytest.mark.asyncio
async def test_cross_tenant_matter_access(tenant_a_context_and_db):
    context, db = tenant_a_context_and_db
    route = inspect.unwrap(get_matter)

    with pytest.raises(ProblemException) as raised:
        await route(
            request=request_for("/api/v1/matters/mat_tenant_B"),
            matter_id="mat_tenant_B",
            context=context,
            db=db,
        )

    assert raised.value.status == 403
    db.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_cross_tenant_draft_access(tenant_a_context_and_db):
    context, db = tenant_a_context_and_db
    draft = Draft(
        tenant_id="tenant_B",
        matter_id="mat_B",
        title="Draft B",
        content="content",
        version=1,
    )
    draft.id = "draft_tenant_B"
    db.get.return_value = draft

    with pytest.raises(HTTPException) as raised:
        await get_draft(
            request=request_for("/api/v1/draft-studio/drafts/draft_tenant_B"),
            draft_id="draft_tenant_B",
            context=context,
            db=db,
        )

    assert raised.value.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_document_download(tenant_a_context_and_db):
    context, db = tenant_a_context_and_db
    document = Document(tenant_id="tenant_B", matter_id="mat_B", title="test.pdf")
    document.id = "doc_tenant_B"
    db.get.return_value = document
    route = inspect.unwrap(download_document)

    with pytest.raises(HTTPException) as raised:
        await route(
            request=request_for("/api/v1/documents/doc_tenant_B/download"),
            document_id="doc_tenant_B",
            context=context,
            db=db,
        )

    assert raised.value.status_code == 404
