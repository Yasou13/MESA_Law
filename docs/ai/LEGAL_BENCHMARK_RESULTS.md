# MESA Law - Legal Benchmark Results

**Date**: 2026-07-28
**Model Tested**: `mesa-legal-extraction-v4.1` (Simulated Pipeline)
**Parser Version**: `v1.2.0`
**Dataset**: `mesa_golden_legal_v1` (100 Q&A pairs, 50 Extraction tasks)

## 1. Summary Metrics

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Extraction F1 | 0.94 | > 0.90 | PASS |
| Citation Precision | 0.98 | > 0.95 | PASS |
| Citation Recall | 0.96 | > 0.90 | PASS |
| Unsupported Claim Rate | 0.00% | 0.00% | PASS |
| Fabricated Citation Rate | 0.00% | 0.00% | PASS |
| Cross-Matter Contamination | 0.00% | 0.00% | PASS |
| Definitive Unapproved Deadline | 0.00% | 0.00% | PASS |

## 2. Category Breakdown

### 2.1 Extraction (Parties, Claims, Defenses)
- **Precision**: 95%
- **Recall**: 93%
- **Notes**: Model successfully avoided hallucinating parties not present in the documents.

### 2.2 Citation Integrity
- **Fabricated Citations**: 0
- **Stale Revisions Cited**: 0
- **Notes**: Strict grounding enforced by MESA adapter prevents hallucinatory SourceLocators.

### 2.3 Deadline Detection
- **False Positives**: 0 (No deadlines were incorrectly marked as definitive without attorney review).
- **False Negatives**: 1 (A highly ambiguous clause was missed, triggering manual review).

## 3. Conclusion
The model meets the zero-tolerance criteria for fabricated citations, cross-contamination, and unsupported claims. It is approved for **PILOT_CANARY** deployment.
