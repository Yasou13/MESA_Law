# Stage 8 Verification — Unified Frontend Data Layer

Recorded on 2026-08-01 on branch `codex/mesa-v4-mvp`. These results cover
the Law-side frontend/API contract work only and do not establish an overall
release `GO`.

## Passing gates

| Gate | Result |
| --- | --- |
| `pnpm --dir apps/web typecheck` | PASS (exit 0) |
| `pnpm --dir apps/web lint` | PASS (exit 0) |
| `pnpm --dir apps/web test:unit` | PASS (5 tests) |
| `pnpm --dir apps/web build` | PASS, offline webpack production build |
| `pnpm --dir apps/web test` | PASS (1 Playwright flow, 1 worker, contract-faithful Law-side stub) |
| `.venv/bin/python -m compileall -q apps scripts tests` | PASS |
| `.venv/bin/ruff check apps scripts` | PASS |
| Targeted mypy for 19 changed Python sources | PASS |
| `.venv/bin/python scripts/export_openapi.py --check` | PASS; current contract and unique operation IDs |
| Orval regeneration comparison | PASS; generated diff identical before and after generation |
| `.venv/bin/alembic heads` | PASS; one head (`a1d7e3c90b42`) |
| `.venv/bin/alembic upgrade head --sql` | PASS; full offline SQL generated |
| Service-independent backend suite | PASS (41 tests) |
| `tests/test_deadline_engine.py` | PASS (6 tests) |

The Playwright scenario covers the Keycloak entry surface, firm selection,
matter creation, MESA binding/preflight, immutable presigned upload, a
versioned review decision using `expected_version`, sourced QA citations, and
the explicitly unavailable external-research surface. It does not start or
simulate a live MESA Core process.

## Open gates

- `.venv/bin/ruff check apps scripts tests` is **FAIL**, with 18 findings in
  pre-existing test files. This remains an internal NO-GO and is assigned to
  the final fail-closed repair cycle.
- The unfiltered pytest suite is **NOT PASSED**. Legacy service E2E tests wait
  for unavailable PostgreSQL/Keycloak/MinIO dependencies, and the legacy
  degraded-mode test contains exception-swallowing behavior. A timeout or a
  skipped test is not recorded as a pass.
- Next.js emits non-fatal warnings about multiple workspace lockfiles, the
  middleware naming convention, and `next start` with standalone output.
  Runtime-profile cleanup remains in the operations stage.
- Live integration with the read-only external MESA Core checkout has not been
  run and must not be inferred from the contract-faithful stub result.

Current decision: **NO-GO** until the remaining internal release gates are
repaired and rerun. If only live external Core integration remains afterward,
the required terminal status is
`LAW-SIDE READY / OVERALL NO-GO — EXTERNAL MESA CORE INTEGRATION PENDING`.
