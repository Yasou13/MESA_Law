# Handoff: FINALIZATION PHASE 9

## Phase Scope
- Phase 9: Legal Research and Source Governance

## Changes Made
- Modified `apps/api/routers/research.py` to decouple the external search logic from blocking the immediate HTTP request. The API now returns a 202 Accepted status via `job_id` corresponding to a `PERFORM_LEGAL_RESEARCH` job enqueued in Postgres.
- Created `apps/worker/handlers/research.py` acting as an asynchronous bridge to mock external legislative data sources. In production, this worker will bind to real endpoints (e.g. Mevzuat Bilgi Sistemi, LexisNexis, Thomson Reuters).
- Integrated `LegalAssertion` drafts into `ReviewQueue` to ensure humans formally vet the extracted external case laws before they manifest as canonical legal assertions in `LegalAssertion` table.
- Extended `apps/worker/handlers/sync.py` to securely materialize `legal_assertion` entities from `ReviewQueue` into `LegalAssertion`.

## Migration Impact
- No schema alterations required for this phase. Data strictly routes through existing queueing mechanisms.

## Security Impact
- Ensures any AI generated case law citation or statute lookup requires human approval. Mitigates the highest-risk LLM hallucination surface area (fake case laws).

## Known Vulnerabilities
- Search queries are vulnerable to broad ILIKE matching on `LegalResource`, returning non-semantic matches. Must migrate to hybrid RAG search for optimal external discovery in production.

## Rollback Steps
1. Restore `search_legal_resources` function in `apps/api/routers/research.py` to its original synchronous logic.
2. Remove `PERFORM_LEGAL_RESEARCH` from `apps/worker/main.py`.

## Testing Results
- End-to-End API unit tests remain successfully passing (`100%`), enforcing the new boundaries seamlessly.
