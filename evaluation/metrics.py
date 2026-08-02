"""
MESA Law Evaluation Metrics — computes real F1, precision, recall, and domain-specific legal metrics.

This module provides the core evaluation logic that replaces the previously hardcoded metrics.
All functions take (predicted, expected) pairs and return float scores in [0.0, 1.0].
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("evaluation.metrics")


@dataclass
class MetricResult:
    """Single metric result with pass/fail gate."""

    name: str
    score: float
    threshold: float
    passed: bool
    detail: str = ""


@dataclass
class EvaluationReport:
    """Full evaluation report across all benchmarks."""

    metrics: list[MetricResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(m.passed for m in self.metrics)

    @property
    def critical_failures(self) -> list[MetricResult]:
        return [m for m in self.metrics if not m.passed]

    def summary(self) -> dict:
        return {
            "total_metrics": len(self.metrics),
            "passed": sum(1 for m in self.metrics if m.passed),
            "failed": sum(1 for m in self.metrics if not m.passed),
            "all_passed": self.all_passed,
            "scores": {m.name: m.score for m in self.metrics},
        }


# ---------------------------------------------------------------------------
# Core metric functions
# ---------------------------------------------------------------------------


def compute_f1(predicted_set: set[str], expected_set: set[str]) -> float:
    """
    Compute token-level F1 between predicted and expected string sets.
    Used for entity extraction, answer content evaluation, etc.
    """
    if not expected_set and not predicted_set:
        return 1.0
    if not expected_set or not predicted_set:
        return 0.0

    tp = len(predicted_set & expected_set)
    fp = len(predicted_set - expected_set)
    fn = len(expected_set - predicted_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)


def compute_precision(predicted_set: set[str], expected_set: set[str]) -> float:
    """Precision: fraction of predicted items that are correct."""
    if not predicted_set:
        return 1.0 if not expected_set else 0.0
    tp = len(predicted_set & expected_set)
    return tp / len(predicted_set)


def compute_recall(predicted_set: set[str], expected_set: set[str]) -> float:
    """Recall: fraction of expected items that were predicted."""
    if not expected_set:
        return 1.0
    tp = len(predicted_set & expected_set)
    return tp / len(expected_set)


# ---------------------------------------------------------------------------
# Citation integrity metrics
# ---------------------------------------------------------------------------


def compute_citation_precision(
    cited_document_ids: list[str],
    valid_document_ids: set[str],
) -> float:
    """
    Fraction of cited documents that actually exist in the matter's document set.
    A score < 1.0 means fabricated citations were produced.
    """
    if not cited_document_ids:
        return 1.0  # No citations is not a fabrication

    valid_count = sum(1 for cid in cited_document_ids if cid in valid_document_ids)
    return valid_count / len(cited_document_ids)


def compute_citation_recall(
    cited_document_ids: list[str],
    expected_document_ids: set[str],
) -> float:
    """
    Fraction of expected source documents that were actually cited.
    """
    if not expected_document_ids:
        return 1.0

    cited_set = set(cited_document_ids)
    found = len(cited_set & expected_document_ids)
    return found / len(expected_document_ids)


def compute_fabricated_citation_rate(
    cited_references: list[dict],
    available_documents: list[dict],
) -> float:
    """
    Rate of citations referencing non-existent documents or impossible page numbers.
    Returns 0.0 for a perfect score (no fabrications).

    Each cited_reference: {"document_id": str, "page_number": int}
    Each available_document: {"id": str, "total_pages": int}
    """
    if not cited_references:
        return 0.0

    doc_page_map = {d["id"]: d["total_pages"] for d in available_documents}
    fabricated = 0

    for ref in cited_references:
        doc_id = ref.get("document_id", "")
        page = ref.get("page_number", 0)

        if doc_id not in doc_page_map:
            fabricated += 1
            logger.warning(f"Fabricated citation: document '{doc_id}' does not exist")
        elif page > doc_page_map[doc_id] or page < 1:
            fabricated += 1
            logger.warning(
                f"Fabricated citation: page {page} exceeds document '{doc_id}' "
                f"total pages ({doc_page_map[doc_id]})"
            )

    return fabricated / len(cited_references)


def compute_cross_matter_contamination_rate(
    response_text: str,
    forbidden_terms: list[str],
) -> float:
    """
    Checks if the response contains information from other matters.
    Returns 0.0 for clean (no contamination), 1.0 for fully contaminated.
    """
    if not forbidden_terms:
        return 0.0

    response_lower = response_text.lower()
    contaminated = sum(1 for term in forbidden_terms if term.lower() in response_lower)
    return contaminated / len(forbidden_terms)


# ---------------------------------------------------------------------------
# Answer quality metrics
# ---------------------------------------------------------------------------


def compute_answer_coverage(
    answer_text: str,
    must_contain: list[str],
    must_not_contain: list[str] | None = None,
) -> tuple[float, list[str]]:
    """
    Check answer coverage: what fraction of must_contain terms appear in the answer.
    Returns (coverage_score, list_of_missing_terms).
    """
    if not must_contain:
        return 1.0, []

    answer_lower = answer_text.lower()
    found = 0
    missing = []

    for term in must_contain:
        if term.lower() in answer_lower:
            found += 1
        else:
            missing.append(term)

    coverage = found / len(must_contain)

    # Check must_not_contain (violations reduce score)
    if must_not_contain:
        violations = sum(1 for term in must_not_contain if term.lower() in answer_lower)
        if violations > 0:
            penalty = violations / len(must_not_contain)
            coverage = max(0.0, coverage - penalty)

    return coverage, missing


def compute_unsupported_claim_rate(
    answer_claims: list[str],
    source_texts: list[str],
) -> float:
    """
    Rate of claims in the answer that cannot be traced to any source text.
    Simple containment check — a claim is "supported" if any source text
    contains a significant portion of its key terms.

    Returns 0.0 for perfect (all claims supported).
    """
    if not answer_claims:
        return 0.0

    combined_sources = " ".join(s.lower() for s in source_texts)
    unsupported = 0

    for claim in answer_claims:
        claim_words = set(claim.lower().split())
        # Remove stop words (Turkish + English basics)
        stop_words = {
            "bir",
            "ve",
            "ile",
            "için",
            "da",
            "de",
            "bu",
            "o",
            "the",
            "is",
            "a",
            "an",
            "in",
            "of",
        }
        meaningful_words = claim_words - stop_words

        if not meaningful_words:
            continue

        found_count = sum(1 for w in meaningful_words if w in combined_sources)
        support_ratio = found_count / len(meaningful_words)

        if support_ratio < 0.5:
            unsupported += 1
            logger.warning(
                f"Unsupported claim: '{claim[:80]}...' (support ratio: {support_ratio:.2f})"
            )

    return unsupported / len(answer_claims)


# ---------------------------------------------------------------------------
# Extraction metrics
# ---------------------------------------------------------------------------


def compute_entity_extraction_f1(
    predicted_entities: list[dict],
    expected_entities: list[dict],
    match_key: str = "name",
) -> float:
    """
    F1 for entity extraction (parties, claims, evidence).
    Matches entities by a key field (default: 'name') using fuzzy containment.
    """
    if not expected_entities and not predicted_entities:
        return 1.0
    if not expected_entities or not predicted_entities:
        return 0.0

    predicted_keys = set()
    for e in predicted_entities:
        val = e.get(match_key, "")
        if isinstance(val, str):
            predicted_keys.add(val.lower().strip())

    expected_keys = set()
    for e in expected_entities:
        val = e.get(match_key, "")
        if isinstance(val, str):
            expected_keys.add(val.lower().strip())

    # Fuzzy matching: a predicted key matches an expected key if one contains the other
    matched_expected = set()
    matched_predicted = set()

    for pk in predicted_keys:
        for ek in expected_keys:
            if pk in ek or ek in pk:
                matched_expected.add(ek)
                matched_predicted.add(pk)

    tp = len(matched_expected)
    fp = len(predicted_keys) - len(matched_predicted)
    fn = len(expected_keys) - len(matched_expected)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)


def compute_role_accuracy(
    predicted_entities: list[dict],
    expected_entities: list[dict],
) -> float:
    """
    For party extraction: fraction of correctly identified entities that also have correct roles.
    """
    if not expected_entities:
        return 1.0

    expected_map = {}
    for e in expected_entities:
        name = e.get("name", "").lower().strip()
        role = e.get("role", "").upper().strip()
        if name:
            expected_map[name] = role

    correct_roles = 0
    matched = 0

    for p in predicted_entities:
        pred_name = p.get("name", "").lower().strip()
        pred_role = p.get("role", "").upper().strip()

        # Fuzzy name match
        for exp_name, exp_role in expected_map.items():
            if pred_name in exp_name or exp_name in pred_name:
                matched += 1
                if pred_role == exp_role:
                    correct_roles += 1
                break

    return correct_roles / matched if matched > 0 else 0.0


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------

# Default thresholds for PILOT_CANARY approval
DEFAULT_GATES = {
    "extraction_f1": 0.80,
    "party_role_accuracy": 0.85,
    "citation_precision": 0.95,
    "citation_recall": 0.80,
    "answer_coverage": 0.75,
    "fabricated_citation_rate": 0.0,  # Must be exactly 0
    "cross_matter_contamination_rate": 0.0,  # Must be exactly 0
    "unsupported_claim_rate": 0.05,  # Max 5%
}


def evaluate_gate(
    metric_name: str,
    score: float,
    threshold: float | None = None,
    is_inverse: bool = False,
) -> MetricResult:
    """
    Evaluate a single metric against its gate threshold.
    is_inverse: True for metrics where lower is better (e.g., fabricated_citation_rate).
    """
    if threshold is None:
        threshold = DEFAULT_GATES.get(metric_name, 0.70)

    if is_inverse:
        passed = score <= threshold
    else:
        passed = score >= threshold

    return MetricResult(
        name=metric_name,
        score=score,
        threshold=threshold,
        passed=passed,
        detail=f"{'PASS' if passed else 'FAIL'}: {score:.4f} {'<=' if is_inverse else '>='} {threshold}",
    )
