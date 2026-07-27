# Frontend Baseline Audit Report

## 1. Static Checks
- **Lint**: PASSED. Warnings fixed.
- **Typecheck**: PASSED.

## 2. Hardcoded URLs & Mocks
- Found `http://localhost:8000` hardcoded in `src/services/api.ts` which bypasses the centralized axios instance.
- Found mock usage in `/deadlines/page.tsx` and `/drafts/page.tsx` (`alert("Listelendi (Mock).")`).
- Found `localStorage.setItem('mesa_tenant_id', ...)` in `/login/page.tsx` which violates Phase 3 (Tenant/Token in LocalStorage).

## 3. Architecture Deviations
- `app/login/page.tsx` manually fetches mock tenant logic instead of real NextAuth credentials logic or Keycloak OIDC.
- Missing `/(auth)` and `/(protected)` route groups.
- `NextAuth` is partially configured but still exposes issuer logic pointing directly to Keycloak instead of routing through robust session handling.

## 4. Remediation Plan
- Delete `src/services/api.ts` since `lib/axios.ts` combined with `orval` is the single source of truth.
- Refactor the whole `app/` folder to use `/(auth)` and `/(protected)`.
- Strip `localStorage` usage completely.
