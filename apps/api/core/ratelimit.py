import os
import sys
from slowapi import Limiter
from slowapi.util import get_remote_address

from apps.api.core.config import settings

redis_url = settings.redis_url

is_testing = (
    "pytest" in sys.modules
    or "_pytest" in sys.modules
    or any("pytest" in arg for arg in sys.argv)
    or os.getenv("MESA_LAW_ENVIRONMENT") == "test"
    or redis_url == "memory://"
)

if is_testing:
    storage_uri = "memory://"
else:
    storage_uri = redis_url

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)


