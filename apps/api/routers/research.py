from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.core.database import get_db
from apps.api.core.ratelimit import limiter
from apps.api.models.research import LegalResource

router = APIRouter(tags=["research"])

@router.get("/search", operation_id="searchLegalResources")
@limiter.limit("60/minute")
async def search_legal_resources(
    request: Request,
    query: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(LegalResource).where(
        or_(
            LegalResource.title.ilike(f"%{query}%"),
            LegalResource.content.ilike(f"%{query}%"),
            LegalResource.citation.ilike(f"%{query}%")
        )
    ).limit(10)
    
    result = await db.execute(stmt)
    resources = result.scalars().all()
    
    if resources:
        return [
            {
                "id": str(r.id),
                "type": "Legislation" if "Kanun" in r.title or "Madde" in r.title else "Case Law",
                "title": r.title,
                "snippet": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                "matchScore": 95
            }
            for r in resources
        ]
        
    return []
