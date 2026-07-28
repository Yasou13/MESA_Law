# MESA Law - Legal Pilot Baseline Audit

## 1. Environment Status
- **Git Branch:** master
- **Recent Commit:** feat: add app icons and replace logos in UI
- **Python Typecheck:** Passes with minor unused/unsorted import warnings (Ruff found 179 non-critical styling errors).
- **Frontend Build:** Turbopack builds successfully, but eslint reports 8 unescaped entities and 4 warnings (no-img-element, exhaustive-deps).
- **Database:** Alembic heads present from earlier phases.

## 2. P0/P1 Issue Verification
- `localStorage.getItem('mesa_tenant_id')` is actively used in `apps/web/src/lib/api/client.ts` and `apps/web/src/components/Sidebar.tsx`.
- Review endpoint currently has mixed responsibilities (worker/API mismatch).
- RLS tests lack tenant A vs B isolation validation.
- Missing `SourceLocator` and detailed `Matter` entity relationships.

## 3. Module Classification
| Module | Status | Notes |
|---|---|---|
| RBAC & Policies | SCAFFOLDED | Enums inconsistent (admin/lawyer vs FIRM_ADMIN). Policies exist but not enforced uniformly. |
| RLS Database Roles | NOT_STARTED | API runs with generic DB user. No NOBYPASSRLS segregation. |
| Review State Machine | SCAFFOLDED | Missing PUBLISHED / PUBLICATION_FAILED robust transitions. |
| Canonical Pipeline | IMPLEMENTED | Drafts exist, but Review->Canonical has dual writes/race conditions. |
| SourceLocator Model | NOT_STARTED | Citations use string snippets instead of structured FK locators. |
| Review Center UI | SCAFFOLDED | Lacking robust /reviews route with conflict check actions. |
| Tenant Session | NOT_STARTED | Using local storage and x-tenant-id headers instead of secure cookies. |
| Conflict Check | NOT_STARTED | No prior matter/party collision logic implemented. |

## 4. Conclusion
System is **NOT** a controlled pilot candidate. Phase 1-20 transformations are required to achieve Legal Product readiness.
