.PHONY: lint test openapi openapi-check release-gate dev-doctor

lint:
	@echo "Running linters..."
	uv run ruff check apps/api apps/worker
	pnpm --filter ./apps/web lint

test:
	@echo "Running tests..."
	uv run pytest apps/api apps/worker
	pnpm --filter ./apps/web test

openapi:
	uv run python scripts/export_openapi.py

openapi-check:
	uv run python scripts/export_openapi.py --check

release-gate:
	./run_all_tests.sh

dev-doctor:
	@echo "Checking development environment..."
	uv --version
	pnpm --version
	node --version
	python3 --version
	@echo "Checking Docker Compose services..."
	docker compose --profile core ps
