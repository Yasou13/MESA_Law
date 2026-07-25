# MESA Law Naming Registry

This registry defines the standard naming conventions for the MESA Law project to ensure consistency across the stack.

## General
- **Product Name:** MESA Law
- **Repository Name:** MESA_Law (or MESA-Law)
- **Python Project Name:** mesa-law

## Services (Docker & Kubernetes)
- **API Backend:** `mesa-law-api` (formerly `legal-api`)
- **Worker:** `mesa-law-worker` (formerly `legal-worker`)
- **Web Frontend:** `mesa-law-web` (formerly `web`)

## Databases & Storage
- **PostgreSQL Database:** `mesa_law`
- **MinIO Bucket:** `mesa-law-docs`

## Environment Variables Prefix
All application-specific environment variables MUST use the `MESA_LAW_` prefix.

### Core Variables
- `MESA_LAW_ENVIRONMENT` (e.g., development, staging, production)
- `MESA_LAW_DATABASE_URL` (instead of `POSTGRES_DB` or `DATABASE_URL`)
- `MESA_LAW_API_PORT` (instead of `API_PORT` or hardcoded `8001`)
- `MESA_LAW_SECRET_KEY` (instead of `secret_key`)

### Intelligence Adapters
- `MESA_LAW_INTELLIGENCE_ADAPTER` (values: `mock`, `postgres_lexical`, `mesa_v4`)
- `MESA_LAW_MESA_API_KEY`
- `MESA_LAW_MESA_BACKEND_URL`

### Object Storage
- `MESA_LAW_STORAGE_ENDPOINT`
- `MESA_LAW_STORAGE_ACCESS_KEY`
- `MESA_LAW_STORAGE_SECRET_KEY`
- `MESA_LAW_STORAGE_BUCKET` (default: `mesa-law-docs`)
