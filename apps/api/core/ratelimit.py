import os
from slowapi import Limiter
from slowapi.util import get_remote_address

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Determine storage_uri based on environment. If not provided or mock, use memory
storage_uri = redis_url if redis_url else "memory://"

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
