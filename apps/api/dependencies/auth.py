import urllib.request
import json
from functools import lru_cache
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from apps.api.core.config import settings
from apps.api.core.models import RequestContext
from apps.api.core.rls import set_tenant_id
from apps.api.core.database import get_db
from apps.api.models.domain import User, Membership

security = HTTPBearer()

@lru_cache(maxsize=1)
def get_jwks():
    try:
        with urllib.request.urlopen(settings.keycloak_jwks_url) as response:
            return json.loads(response.read())
    except Exception as e:
        return {"keys": []}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        jwks = get_jwks()
        payload = jwt.decode(
            token, 
            jwks, 
            algorithms=["RS256"], 
            audience=[settings.keycloak_client_id, "account"],
            options={"verify_aud": True, "verify_exp": True}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])
        
        return {"id": user_id, "roles": set(roles), "email": payload.get("email")}
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from e

async def setup_tenant_context(
    request: Request,
    x_tenant_id: Optional[str] = Header(default=None, alias="x-tenant-id"),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    keycloak_id = user["id"]
    
    # Check User
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    # Check Membership with active status and deterministic ordering
    query = select(Membership).where(
        Membership.user_id == db_user.id,
        Membership.is_active == True
    ).order_by(Membership.created_at.asc())
    
    if x_tenant_id:
        query = query.where(Membership.firm_id == x_tenant_id)
        
    mem_result = await db.execute(query)
    membership = mem_result.scalars().first()
    
    if not membership:
        if x_tenant_id:
            raise HTTPException(status_code=403, detail=f"User is not an active member of requested firm {x_tenant_id}")
        raise HTTPException(status_code=403, detail="User is not an active member of any firm")
        
    tenant_id = membership.firm_id
    firm_role = membership.role
    
    set_tenant_id(tenant_id)
    try:
        await db.execute(text(f"SET SESSION app.current_tenant = '{tenant_id}';"))
    except Exception as e:
        import logging
        logging.error(f"Failed to execute SET SESSION app.current_tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize tenant security context") from e

    return RequestContext(
        tenant_id=tenant_id,
        principal_id=db_user.id,
        roles={firm_role} if firm_role else user["roles"]
    )
