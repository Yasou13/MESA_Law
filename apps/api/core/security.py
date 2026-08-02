from apps.api.core.config import settings
from apps.api.core.errors import ProblemException
from fastapi import Depends, Request
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel


class CsrfSettings(BaseModel):
    secret_key: str = settings.secret_key
    cookie_samesite: str = "lax"
    cookie_secure: bool = settings.env != "development"


@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()


async def verify_csrf(request: Request, csrf_protect: CsrfProtect = Depends()):
    if request.method not in ["GET", "HEAD", "OPTIONS", "TRACE"]:
        try:
            await csrf_protect.validate_csrf(request)
        except CsrfProtectError:
            raise ProblemException(
                status=403, title="Forbidden", detail="CSRF validation failed"
            )
