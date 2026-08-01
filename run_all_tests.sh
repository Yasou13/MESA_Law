#!/usr/bin/env bash
set -euo pipefail

echo "======================================"
echo " MESA Law Production Hardening Checks"
echo "======================================"

echo "1. Running Linter (Ruff)..."
uv run --frozen ruff check apps/ tests/

echo "2. Checking formatting (Ruff)..."
uv run --frozen ruff format --check apps/ tests/

echo "3. Running Security Static Analysis (Bandit)..."
# Exclude tests from bandit
uv run --frozen bandit -r apps/ -c pyproject.toml

echo "4. Running type checks (Mypy)..."
uv run --frozen mypy apps

echo "5. Running Python compile check..."
uv run --frozen python -m compileall -q apps tests evaluation

echo "6. Running Pytest Test Suite..."
# Run all tests via uv pytest with OpenTelemetry disabled to prevent DNS errors
OTEL_SDK_DISABLED=true uv run --frozen pytest apps tests --ignore=tests/e2e -v

echo "7. Checking Database Migrations..."
# This ensures alembic is up to date
uv run --frozen alembic heads
uv run --frozen alembic check

echo "======================================"
echo " ALL REQUIRED LOCAL QUALITY GATES PASSED "
echo " This does not include the external MESA Core integration gate."
echo "======================================"
