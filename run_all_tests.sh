#!/usr/bin/env bash
set -euo pipefail
export MESA_LAW_ENVIRONMENT=test
export MESA_LAW_E2E_STUB=1
export MESA_LAW_OBSERVABILITY_ENABLED=false
export OTEL_SDK_DISABLED=true
: "${MESA_LAW_DATABASE_URL:?Set MESA_LAW_DATABASE_URL to a migrated, isolated PostgreSQL test database}"

echo "======================================"
echo " MESA Law Production Hardening Checks"
echo "======================================"

echo "1. Running Linter (Ruff)..."
uv run --frozen ruff check apps tests scripts evaluation

echo "2. Checking formatting (Ruff)..."
uv run --frozen ruff format --check apps tests scripts evaluation

echo "3. Running Security Static Analysis (Bandit)..."
# Exclude tests from bandit
uv run --frozen bandit -q -r apps \
  -x 'apps/api/test_*.py,apps/worker/test_*.py' \
  -c pyproject.toml

echo "4. Running type checks (Mypy)..."
uv run --frozen mypy apps scripts

echo "5. Running Python compile check..."
uv run --frozen python -m compileall -q apps tests evaluation

echo "6. Running Pytest Test Suite..."
# Run all tests via uv pytest with OpenTelemetry disabled to prevent DNS errors
timeout 180s uv run --frozen pytest apps tests --ignore=tests/e2e -v

echo "7. Checking Alembic and OpenAPI contracts..."
uv run --frozen python scripts/check_alembic.py
uv run --frozen python scripts/export_openapi.py --check

echo "8. Running frontend lint, types, units, generation drift, and offline build..."
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test:unit
pnpm --dir apps/web api:generate
git diff --exit-code -- apps/web/src/api
pnpm --dir apps/web build

echo "9. Validating bounded Compose profiles without pulling images..."
docker compose --env-file .env.example -f docker-compose.yml config --quiet
docker compose --env-file .env.example -f docker-compose.full.yml config --quiet
docker compose --env-file .env.example -f docker-compose.lite.yml config --quiet
docker compose --env-file .env.example -f docker-compose.integration.yml config --quiet

echo "10. Checking host resources and running one-worker Law-side browser acceptance..."
uv run --frozen python scripts/check_resources.py
pnpm --dir apps/web test

echo "======================================"
echo " ALL REQUIRED LOCAL QUALITY GATES PASSED "
echo " External MESA Core build/start/live integration was not run and is not passed."
echo "======================================"
