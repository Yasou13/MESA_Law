from datetime import UTC

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import get_current_user, setup_tenant_context
from apps.api.models.domain import User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me")
async def get_current_user_profile(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    keycloak_id = user["id"]
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": db_user.id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "roles": list(user.get("roles", [])),
        "is_support_access_granted": db_user.is_support_access_granted,
        "support_access_granted_until": db_user.support_access_granted_until.isoformat() if db_user.support_access_granted_until else None
    }

class UpdateUserProfileRequest(BaseModel):
    full_name: str | None = None
    email: str | None = None

@router.put("/me", operation_id="updateCurrentUserProfile")
async def update_current_user_profile(
    payload: UpdateUserProfileRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    keycloak_id = user["id"]
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if payload.full_name is not None:
        db_user.full_name = payload.full_name
    if payload.email is not None:
        db_user.email = payload.email
        
    await db.commit()
    await db.refresh(db_user)
    
    return {
        "id": db_user.id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "roles": list(user.get("roles", [])),
        "is_support_access_granted": db_user.is_support_access_granted,
        "support_access_granted_until": db_user.support_access_granted_until.isoformat() if db_user.support_access_granted_until else None
    }

class SupportAccessRequest(BaseModel):
    duration_hours: int = 24

@router.post("/me/support-access", operation_id="grantSupportAccess")
async def grant_support_access(
    payload: SupportAccessRequest,
    context: RequestContext = Depends(setup_tenant_context),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from apps.api.core.policies import AdminAccessPolicy
    AdminAccessPolicy.can_manage_firm(context)

    from datetime import datetime, timedelta
    
    keycloak_id = user["id"]
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db_user.is_support_access_granted = True
    db_user.support_access_granted_until = datetime.now(UTC) + timedelta(hours=payload.duration_hours)
    
    await db.commit()
    
    return {
        "status": "granted",
        "is_support_access_granted": db_user.is_support_access_granted,
        "support_access_granted_until": db_user.support_access_granted_until.isoformat()
    }
