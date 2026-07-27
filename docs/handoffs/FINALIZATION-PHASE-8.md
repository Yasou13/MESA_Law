# Handoff: FINALIZATION PHASE 8

## Phase Scope
- Phase 8: Matter Q&A and Retrieval

## Changes Made
- Transferred `fts_vector` target from the coarse `ParsedPage` level to the precise `DocumentChunk` model. This enables hyper-local context retrieval (e.g., retrieving an exact paragraph rather than an entire PDF page).
- Refactored `apps/api/core/qa.py` and `apps/api/adapters/pg_intelligence.py` to route search parameters using PostgreSQL `websearch_to_tsquery` matched against `document_chunks`.
- Added the missing `/matters/{matter_id}/qa` router mapped to `ask_matter_question` within `apps/api/routers/matters.py`.
- Fixed the Alembic migration bug preventing cast coercion (`event_date` to `DateTime`).

## Migration Impact
- Fixed `f1a2b3c4d5e6` missing `DROP POLICY` safeguard.
- Generated `0fb531054f20` mapping new structures. Required a manual override on the DB cast macro (`postgresql_using='event_date::timestamp with time zone'`). All applied effectively to the local test database via `alembic upgrade head`.

## Security Impact
- Queries strictly pass through `matter_id` enforced conditions, ensuring users cannot bypass tenant or case scope isolations.

## Known Vulnerabilities
- `websearch_to_tsquery` relies on 'turkish' stemmer. Certain complex legal abbreviations may require a custom postgres dictionary to avoid stemming over-simplification.
- LLM response generation in `ask_matter_question` is mocked statically. Will require physical LangChain/LlamaIndex LLM binding upon production environment setup.

## Rollback Steps
1. Delete endpoint `/matters/{matter_id}/qa` from `matters.py`.
2. Downgrade Alembic schema via `alembic downgrade acfdad206beb`.

## Testing Results
- API tests spanning QA boundaries and RLS isolation succeed (`100%`).
