from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.ratelimit import limiter
from apps.api.dependencies.auth import get_current_user, setup_tenant_context
from apps.api.models.domain import Firm, Membership, User

router = APIRouter()

class FirmCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class FirmResponse(BaseModel):
    id: str
    name: str

@router.get("/firms", response_model=list[FirmResponse], operation_id="listUserFirms")
@limiter.limit("60/minute")
async def list_user_firms(
    request: Request,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    keycloak_id = user["id"]
    db_user_res = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = db_user_res.scalars().first()
    if not db_user:
        return []
        
    mem_res = await db.execute(
        select(Firm).join(Membership, Membership.firm_id == Firm.id).where(
            Membership.user_id == db_user.id,
            Membership.is_active == True
        )
    )
    firms = mem_res.scalars().all()
    return [{"id": f.id, "name": f.name} for f in firms]

@router.get("/firms/members", operation_id="listFirmMembers")
@limiter.limit("60/minute")
async def list_firm_members(
    request: Request,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    mem_res = await db.execute(
        select(Membership, User).join(User, Membership.user_id == User.id)
        .where(Membership.firm_id == context.tenant_id)
    )
    results = mem_res.all()
    return [{
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": mem.role,
        "is_active": mem.is_active
    } for mem, user in results]

@router.get("/firms/{firm_id}", response_model=FirmResponse, operation_id="getFirmDetails")
@limiter.limit("60/minute")
async def get_firm_details(
    request: Request,
    firm_id: str,
    context: RequestContext = Depends(setup_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    if context.tenant_id != firm_id and "FIRM_ADMIN" not in context.roles:
        raise HTTPException(status_code=403, detail="Access denied to requested firm details")
    firm = await db.get(Firm, firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Firm not found")
    return {"id": firm.id, "name": firm.name}

@router.post("/firms", response_model=FirmResponse, operation_id="createFirm")
@limiter.limit("10/minute")
async def create_firm(
    request: Request,
    req: FirmCreateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    keycloak_id = user["id"]
    db_user_res = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = db_user_res.scalars().first()
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    firm = Firm(name=req.name)
    db.add(firm)
    await db.flush()
    
    membership = Membership(user_id=db_user.id, firm_id=firm.id, role="FIRM_ADMIN", is_active=True)
    db.add(membership)
    await db.commit()
    return {"id": firm.id, "name": firm.name}

