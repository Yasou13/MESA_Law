from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import get_current_user, setup_tenant_context
from apps.api.models.domain import Membership, User
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/session", tags=["Session"])

@router.get("/context")
async def get_session_context(
    context: RequestContext = Depends(setup_tenant_context)
):
    return {
        "status": "success",
        "tenant_id": context.tenant_id,
        "principal_id": context.principal_id,
        "roles": list(context.roles)
    }

@router.post("/active-firm")
async def set_active_firm(
    firm_id: str,
    response: Response,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verified tenant switch flow.
    Validates that the currently authenticated user is an active member of the requested firm.
    Returns the firm details and role, setting a secure server-side cookie.
    """
    keycloak_id = user["id"]
    
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    mem_result = await db.execute(
        select(Membership).where(
            Membership.user_id == db_user.id,
            Membership.firm_id == firm_id,
            Membership.is_active == True
        )
    )
    membership = mem_result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="User is not an active member of the requested firm")
        
    is_secure = settings.env in ["pilot", "staging", "production"]
    
    response.set_cookie(
        key="mesa_active_firm_id",
        value=str(firm_id),
        httponly=True,
        secure=is_secure,
        samesite="lax"
    )
    
    return {
        "status": "success",
        "active_firm_id": str(firm_id),
        "role": membership.role
    }
