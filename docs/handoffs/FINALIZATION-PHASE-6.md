# Handoff: FINALIZATION PHASE 6

## Phase Scope
- Phase 6: Extraction Suggestion and Review Center

## Changes Made
- Modified `apps/worker/handlers/extraction.py` to decouple LLM output from direct transactional commits into `Claim`/`MatterParty` domains.
- Redirected LLM extraction pipeline outputs to `ReviewQueue` (a.k.a `legal_review_queue`) specifically under `draft` status instead of the legacy `pending` state, strictly satisfying Human-in-the-Loop review constraints.
- Bound data provenance (from `DocumentChunk.watermarked_text`) into the LLM context flow, mapping it implicitly into the proposed `ReviewQueue` entities.
- Updated `/api/v1/reviews` API router to exclusively query and handle `draft` reviews to match the new strict workflow lifecycle.

## Migration Impact
- Minimal. Data model mapping migrated away from the deprecated `ReviewItem` interface. No schema altering DDL was necessary for Phase 6 since `legal_review_queue` already exists.

## Security Impact
- Strong boundary established preventing uncontrolled LLM hallucinations from polluting canonical canonical ground-truth data models (`Claim`, `MatterParty`, `TimelineEvent`).
- Every accept/reject/correct event intrinsically logs an immutable trace to `AuditLog`.

## Known Vulnerabilities
- None identified in the scope of Phase 6.

## Rollback Steps
1. Revert `apps/worker/handlers/extraction.py` back to inserting directly into `ReviewItem` (legacy mock entity) or `Claim` models.
2. Revert `status` in `apps/api/routers/reviews.py` to `pending`.

## Testing Results
- `test_reviews.py` passes completely `(100%)`.
- E2E isolation logic validates tenant boundaries properly over `draft` review items.
