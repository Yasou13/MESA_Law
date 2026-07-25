import os
import sys
from slowapi import Limiter
from slowapi.util import get_remote_address

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

is_testing = (
    "pytest" in sys.modules
    or "_pytest" in sys.modules
    or any("pytest" in arg for arg in sys.argv)
    or os.getenv("MESA_ENV") == "test"
    or redis_url == "memory://"
)

if is_testing:
    storage_uri = "memory://"
else:
    storage_uri = redis_url

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)


