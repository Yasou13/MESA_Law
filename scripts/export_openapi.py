"""Export and verify the deterministic FastAPI OpenAPI contract."""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = ROOT / "apps" / "api" / "openapi.json"
sys.path.insert(0, str(ROOT))


def rendered_openapi() -> str:
    os.environ.setdefault("MESA_LAW_ENVIRONMENT", "test")
    from apps.api.main import app

    schema = app.openapi()
    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    duplicates = sorted(
        operation_id
        for operation_id, count in Counter(operation_ids).items()
        if count > 1
    )
    if duplicates:
        raise RuntimeError(f"Duplicate OpenAPI operation IDs: {duplicates}")
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the checked-in OpenAPI document differs from FastAPI.",
    )
    args = parser.parse_args()
    rendered = rendered_openapi()
    if args.check:
        if not OPENAPI_PATH.exists() or OPENAPI_PATH.read_text() != rendered:
            print("OpenAPI drift detected; run scripts/export_openapi.py")
            return 1
        print("OpenAPI contract is current and has unique operation IDs")
        return 0

    OPENAPI_PATH.write_text(rendered)
    print(f"Wrote {OPENAPI_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
