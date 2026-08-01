"""Global test-process defaults applied before application modules are imported."""

import os

os.environ.setdefault("MESA_LAW_ENVIRONMENT", "test")
