from fastapi import APIRouter, Depends
from pydantic import BaseModel
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import setup_tenant_context
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.core.qa import ask_matter_question
from apps.api.core.ratelimit import limiter
from fastapi import Request

router = APIRouter(prefix="/qa", tags=["qa"])

class QAQuery(BaseModel):
    matter_id: str
    question: str

@router.post("/ask", operation_id="askQuestion")
@limiter.limit("20/minute")
async def ask_question(
    request: Request,
    query: QAQuery,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    return await ask_matter_question(db, query.matter_id, query.question)
