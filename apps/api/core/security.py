from fastapi import Request, Depends
from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel
from apps.api.core.config import settings
from apps.api.core.errors import ProblemException

class CsrfSettings(BaseModel):
    secret_key: str = settings.secret_key
    cookie_samesite: str = "lax"
    cookie_secure: bool = False # Should be True in production

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

async def verify_csrf(request: Request, csrf_protect: CsrfProtect = Depends()):
    if request.method not in ["GET", "HEAD", "OPTIONS", "TRACE"]:
        try:
            await csrf_protect.validate_csrf(request)
        except Exception as e:
            raise ProblemException(status=403, title="Forbidden", detail="CSRF validation failed")

async def get_current_user(request: Request):
    """
    Mockable authentication dependency.
    In real usage, verifies Keycloak JWT from session cookie or Authorization header.
    """
    return {"id": "mock-user-id", "roles": ["member"]}
