from apps.api.core.models import RequestContext
from apps.api.core.rls import set_tenant_id
from fastapi import Depends, Header, HTTPException


# In a real app, this would validate a JWT token
async def get_current_user(authorization: str = Header(None)) -> dict:
    # For now, returning a mock user. 
    # Step 9: Make sure it has tenant validation mock if needed
    return {"id": "mock-user-id", "roles": {"member"}}

async def setup_tenant_context(
    tenant_id: str = Header(..., alias="x-tenant-id"), 
    user: dict = Depends(get_current_user)
) -> RequestContext:
    # Basic protection: If the header is just a string, we accept it for local dev but it's now tracked in RequestContext
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing x-tenant-id header")
        
    set_tenant_id(tenant_id)
    return RequestContext(
        tenant_id=tenant_id,
        principal_id=user["id"],
        roles=user["roles"]
    )
