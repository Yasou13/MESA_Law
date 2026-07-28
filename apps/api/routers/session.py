from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_user
from apps.api.models.domain import User, Membership

router = APIRouter(prefix="/session", tags=["Session"])

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
    Returns the firm details and role, which the frontend can then use to set the x-tenant-id header.
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
        
    response.set_cookie(
        key="mesa_tenant_id",
        value=str(firm_id),
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {
        "status": "success",
        "active_firm_id": str(firm_id),
        "role": membership.role
    }
