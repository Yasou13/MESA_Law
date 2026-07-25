# Work Order 009 (WO-009) Handoff

## Objective
Implement the frontend shell and canonical workflow (Login -> Matters -> Upload -> View) for MESA Law.

## Accomplishments
- **Frontend/Backend Integration:** Fully resolved all CORS, Payload format, and Header mapping issues.
  - Orval requests now properly wrap mutations in the `{ data: ... }` format.
  - Axios interceptor now correctly injects the `x-tenant-id` header to avoid default fallbacks.
- **FastAPI Header Resolution Fix:** Identified a subtle edge-case in FastAPI where `Header("default")` auto-converts the parameter name to hyphenated case (e.g. `tenant_id` to `tenant-id`). Updated the dependency to explicitly use `alias="x-tenant-id"` so it correctly maps to the frontend headers.
- **Database Seeding for E2E:** 
  - Added a `seed.py` script to insert the `e2e-tenant-123` into the `firms` table with the required `version_id`.
  - Ensures the E2E tests run successfully without `ForeignKeyViolation`.
- **Storage/MinIO Fixes:**
  - MinIO credentials in `apps/api/core/storage.py` were corrected from `minioadmin` to `admin:password123` (matching the `docker-compose.yml`).
  - Implemented `apps/api/setup_minio.py` to pre-provision the `mesa-law-docs` bucket.
- **E2E Testing:** Playwright tests for the canonical workflow (`canonical.spec.ts`) now **pass 100%**.

## Next Steps
- Implement WO-010 (File Upload & Document Processing) which builds heavily on this storage integration.

All tests have been successfully run against the frontend shell.
