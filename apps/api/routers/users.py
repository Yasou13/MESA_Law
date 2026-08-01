from datetime import UTC, datetime
from typing import Any

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.dependencies.auth import get_current_user, setup_tenant_context
from apps.api.models.domain import User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    email: str
    full_name: str
    roles: list[str]
    is_support_access_granted: bool
    support_access_granted_until: datetime | None


class SupportAccessResponse(BaseModel):
    status: str
    is_support_access_granted: bool
    support_access_granted_until: datetime


@router.get(
    "/me", response_model=UserProfileResponse, operation_id="getCurrentUserProfile"
)
async def get_current_user_profile(
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
        "support_access_granted_until": db_user.support_access_granted_until,
    }


class UpdateUserProfileRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)


@router.put(
    "/me",
    operation_id="updateCurrentUserProfile",
    response_model=UserProfileResponse,
)
async def update_current_user_profile(
    payload: UpdateUserProfileRequest,
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
        "support_access_granted_until": db_user.support_access_granted_until,
    }


class SupportAccessRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    duration_hours: int = Field(default=24, ge=1, le=72)


@router.post(
    "/me/support-access",
    operation_id="grantSupportAccess",
    response_model=SupportAccessResponse,
)
async def grant_support_access(
    payload: SupportAccessRequest,
    context: RequestContext = Depends(setup_tenant_context),
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from apps.api.core.policies import AdminAccessPolicy

    AdminAccessPolicy.can_manage_firm(context)

    from datetime import timedelta

    keycloak_id = user["id"]
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.is_support_access_granted = True
    db_user.support_access_granted_until = datetime.now(UTC) + timedelta(
        hours=payload.duration_hours
    )

    await db.commit()

    return {
        "status": "granted",
        "is_support_access_granted": db_user.is_support_access_granted,
        "support_access_granted_until": db_user.support_access_granted_until,
    }
