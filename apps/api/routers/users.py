from apps.api.core.database import get_db
from apps.api.dependencies.auth import get_current_user
from apps.api.models.domain import User
from fastapi import APIRouter, Depends, HTTPException
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
        "roles": list(user.get("roles", []))
    }
