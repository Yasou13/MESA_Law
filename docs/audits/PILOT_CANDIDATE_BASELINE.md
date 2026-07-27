# Pilot Candidate Baseline Audit

## Git Status
Branch: `master`
Modifications:
- `apps/api/dependencies/auth.py`
- `apps/web/package.json`
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/matters/page.tsx`
- `pyproject.toml`, `uv.lock`, etc.

## Backend (uv, pytest, ruff)
- **compileall**: Works via `uv run python -m compileall`.
- **pytest**: Fails during collection (2 errors):
  - `apps/api/test_reviews.py:16` - IndentationError: unexpected indent
  - `tests/test_deadline_engine.py` - ImportError: cannot import name 'PotentialDeadline' from 'apps.api.models.deadline'
- **ruff**: Not fully run yet, but pytest failures block CI.

## Frontend (pnpm, Next.js)
- **install**: Up to date.
- **lint**: Fails with 3 errors and 2 warnings (react-hooks/set-state-in-effect and missing deps).
- **typecheck**: Script missing in package.json (needs to be added).

## Alembic
- HEAD is at `2fa9a218fa75`.

## Docker Compose
- Config parses successfully, contains internal Keycloak and postgres services.

## Conclusion
The system currently does not pass the basic compile and lint gates. We will address these in Phase 1.
