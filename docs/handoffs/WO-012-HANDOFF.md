# Work Order 012 (WO-012) Handoff

## Objective
Establish the `GoldenLegalPackage` schema to validate the versioned legal package format, legislation normalization, court decision metadata, and anonymization workflows before they can be staged or ingested.

## Accomplishments
- **Pydantic Schemas (`apps/api/schemas/legal_package.py`)**:
  - `SourceManifest`: Validates hash, publisher, and license.
  - `LegislationItem`: Enforces historical normalization fields (`valid_from`, `is_current`, etc.).
  - `CourtDecisionItem`: Captures court metadata and enforces `anonymization_status`.
  - `GoldenLegalPackage`: A root validator that ensures package-wide rules (e.g. `PUBLIC` license demands `ANONYMIZED` status for all decisions) and hash verification.
- **Testing**:
  - `tests/test_legal_package.py` tests all custom Pydantic validators.

## Validation
- `uv run pytest tests/test_legal_package.py` passed (4/4 tests).
- As requested, no actual MESA ingestion is performed; this satisfies the staging requirements.

## Next Suggested Work Order
- **WO-013** (Benchmark governance)
