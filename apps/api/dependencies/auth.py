import os
import urllib.request
import json
from functools import lru_cache
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.core.models import RequestContext
from apps.api.core.rls import set_tenant_id
from apps.api.core.database import get_db
from apps.api.models.domain import User, Membership

security = HTTPBearer()

JWKS_URL = os.getenv("KEYCLOAK_JWKS_URL", "http://localhost:8080/realms/mesa_law/protocol/openid-connect/certs")

@lru_cache(maxsize=1)
def get_jwks():
    try:
        with urllib.request.urlopen(JWKS_URL) as response:
            return json.loads(response.read())
    except Exception as e:
        # Fallback empty jwks, decoding will fail if required
        return {"keys": []}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        if os.getenv("ENVIRONMENT") == "production":
            jwks = get_jwks()
            payload = jwt.decode(
                token, 
                jwks, 
                algorithms=["RS256"], 
                audience="account",
                options={"verify_aud": False} # Or set correct audience
            )
        else:
            payload = jwt.get_unverified_claims(token)
        
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
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    
    keycloak_id = user["id"]
    
    # Check User
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    # Check Membership (Assuming one active firm per user for now)
    mem_result = await db.execute(select(Membership).where(Membership.user_id == db_user.id))
    membership = mem_result.scalars().first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="User is not a member of any firm")
        
    tenant_id = membership.firm_id
    
    set_tenant_id(tenant_id)
    return RequestContext(
        tenant_id=tenant_id,
        principal_id=db_user.id,
        roles=user["roles"]
    )
