import urllib.request
import json
import time
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

_jwks_cache = {"keys": [], "expires_at": 0}

def get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    now = time.time()
    if not force_refresh and _jwks_cache["keys"] and now < _jwks_cache["expires_at"]:
        return _jwks_cache
    try:
        with urllib.request.urlopen(settings.keycloak_jwks_url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            _jwks_cache = {"keys": data.get("keys", []), "expires_at": now + 300}
            return _jwks_cache
    except Exception as e:
        if _jwks_cache["keys"]:
            return _jwks_cache
        return {"keys": []}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if kid and not any(key.get("kid") == kid for key in jwks.get("keys", [])):
            jwks = get_jwks(force_refresh=True)
            
        payload = jwt.decode(
            token, 
            jwks, 
            algorithms=["RS256"], 
            audience=[settings.keycloak_client_id, "account"],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": True, "verify_exp": True, "verify_iss": True}
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
    db: AsyncSession = Depends(get_db)
) -> RequestContext:
    # --- DEV-MODE BYPASS ---
    # In test environments, allow unauthenticated access
    # with a synthetic context for E2E testing without Keycloak.
    auth_header = request.headers.get("authorization")
    is_mock_token = auth_header == "Bearer mock-e2e-token"
    if settings.test_auth_enabled and settings.env == "test" and (not auth_header or is_mock_token):
        dev_tenant = x_tenant_id or "dev-tenant-default"
        set_tenant_id(dev_tenant)
        try:
            # Create dev firm if not exists
            res = await db.execute(text("SELECT id FROM firms WHERE id = :id"), {"id": dev_tenant})
            if not res.scalar():
                await db.execute(
                    text("INSERT INTO firms (id, name, created_at, updated_at, version_id) VALUES (:id, :name, NOW(), NOW(), 1) ON CONFLICT (id) DO NOTHING"),
                    {"id": dev_tenant, "name": "Dev Default Firm"}
                )
                await db.commit()
                
            await db.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(dev_tenant)})
        except Exception as e:
            await db.rollback()
            # Try setting config again after rollback
            try:
                await db.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(dev_tenant)})
            except Exception:
                pass
        return RequestContext(
            tenant_id=dev_tenant,
            principal_id="dev-user-id",
            roles={"FIRM_ADMIN"}
        )
    # --- END DEV-MODE BYPASS ---

    user = await get_current_user(
        await security(request)
    )
    keycloak_id = user["id"]
    
    # Check User
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    x_tenant_id = tenant_id or request.cookies.get("mesa_tenant_id")
    
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
        await db.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(tenant_id)})
    except Exception as e:
        import logging
        logging.error(f"Failed to execute set_config for app.current_tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize tenant security context") from e

    return RequestContext(
        tenant_id=tenant_id,
        principal_id=db_user.id,
        roles={firm_role} if firm_role else user["roles"]
    )
