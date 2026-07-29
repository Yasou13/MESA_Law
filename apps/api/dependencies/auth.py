import json
import time
import urllib.request

from apps.api.core.config import settings
from apps.api.core.database import get_db
from apps.api.core.models import RequestContext
from apps.api.core.rls import set_tenant_id
from apps.api.models.domain import Firm, Membership, User
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

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
    except Exception:
        if _jwks_cache["keys"]:
            return _jwks_cache
        return {"keys": []}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    if token == "dev-mock-token":
        return {"id": "dev-user-id", "roles": {"FIRM_ADMIN", "developer"}, "email": "dev@mesalaw.com", "auth_time": time.time()}

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
            options={"verify_aud": True, "verify_exp": True, "verify_iss": True, "verify_signature": True}
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])
        
        return {"id": user_id, "roles": set(roles), "email": payload.get("email"), "auth_time": payload.get("auth_time")}
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from e

async def require_recent_auth(
    request: Request,
    max_age_seconds: int = 300
) -> None:
    cred = await security(request)
    user = await get_current_user(cred)
    auth_time = user.get("auth_time")
    if not auth_time:
        raise HTTPException(status_code=401, detail="auth_time claim missing in token, re-authentication required")
    
    if time.time() - auth_time > max_age_seconds:
        raise HTTPException(status_code=401, detail="Recent authentication required")

async def setup_tenant_context(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> RequestContext:

    user = await get_current_user(await security(request))
    keycloak_id = user["id"]
    
    if keycloak_id == "dev-user-id":
        # Dev backdoor bypass: ensure a firm and user exist to prevent foreign key constraint errors
        result = await db.execute(select(Firm).limit(1))
        firm = result.scalars().first()
        if not firm:
            firm = Firm(id="e2e-tenant-123", name="Developer Firm")
            db.add(firm)
            await db.commit()
            await db.refresh(firm)
        active_firm_id = firm.id
        
        result_user = await db.execute(select(User).limit(1))
        db_usr = result_user.scalars().first()
        if not db_usr:
            import uuid6
            db_usr = User(id=str(uuid6.uuid7()), email="dev@mesalaw.com", keycloak_id="dev-user-id", full_name="Developer Admin")
            db.add(db_usr)
            await db.commit()
            await db.refresh(db_usr)
        principal_id = db_usr.id

        set_tenant_id(active_firm_id)
        try:
            await db.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(active_firm_id)})
        except Exception:
            pass
        return RequestContext(tenant_id=active_firm_id, principal_id=principal_id, roles={"FIRM_ADMIN", "developer"})
        
    # Resolve user
    result = await db.execute(select(User).where(User.keycloak_id == keycloak_id))
    db_user = result.scalars().first()
    
    if not db_user:
        raise HTTPException(status_code=403, detail="User not registered in the system")
        
    # Phase 2: Resolve server-side active firm from secure cookie
    cookie_tenant_id = request.cookies.get("mesa_active_firm_id")
    
    # Get active memberships
    query = select(Membership).where(
        Membership.user_id == db_user.id,
        Membership.is_active == True
    ).order_by(Membership.created_at.asc())
    
    if cookie_tenant_id:
        query = query.where(Membership.firm_id == cookie_tenant_id)
        
    mem_result = await db.execute(query)
    membership = mem_result.scalars().first()
    
    if not membership:
        if cookie_tenant_id:
            raise HTTPException(status_code=403, detail="User is not an active member of the requested firm context.")
        raise HTTPException(status_code=403, detail="User is not an active member of any firm.")
        
    active_firm_id = membership.firm_id
    firm_role = membership.role
    
    set_tenant_id(active_firm_id)
    try:
        await db.execute(text("SELECT set_config('app.current_tenant', :tenant, true)"), {"tenant": str(active_firm_id)})
    except Exception as e:
        import logging
        logging.error(f"Failed to execute set_config for app.current_tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize tenant security context") from e

    return RequestContext(
        tenant_id=active_firm_id,
        principal_id=db_user.id,
        roles={firm_role} if firm_role else user["roles"]
    )
