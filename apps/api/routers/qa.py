from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.policies import MatterAccessPolicy
from apps.api.core.qa import QAResponse, QuestionRequest, ask_matter_question
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import setup_tenant_context
from apps.api.models.document import Document
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/qa", tags=["qa"])


class QAQuery(QuestionRequest):
    matter_id: str
    document_id: str | None = None


@router.post("/ask", operation_id="askQuestion", response_model=QAResponse)
@limiter.limit("20/minute")
async def ask_question(
    request: Request,
    query: QAQuery,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    await MatterAccessPolicy.can_read(context, db, query.matter_id)
    if query.document_id:
        document = await db.get(Document, query.document_id)
        if (
            not document
            or document.tenant_id != context.tenant_id
            or document.matter_id != query.matter_id
        ):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Document not found")
    return await ask_matter_question(
        db, context.tenant_id, query.matter_id, query.document_id, query.question
    )
