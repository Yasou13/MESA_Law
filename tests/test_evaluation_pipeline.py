"""
Tests for the Evaluation Pipeline — verifies golden dataset validity,
metric computations, and gate evaluation logic.
"""

import json
from pathlib import Path

import pytest
from evaluation.metrics import (
    EvaluationReport,
    compute_answer_coverage,
    compute_citation_precision,
    compute_citation_recall,
    compute_cross_matter_contamination_rate,
    compute_entity_extraction_f1,
    compute_f1,
    compute_fabricated_citation_rate,
    compute_precision,
    compute_recall,
    compute_role_accuracy,
    compute_unsupported_claim_rate,
    evaluate_gate,
)

GOLDEN_DATASET_PATH = (
    Path(__file__).parent.parent / "evaluation" / "golden_dataset.json"
)


# ---------------------------------------------------------------------------
# Golden Dataset Integrity Tests
# ---------------------------------------------------------------------------


class TestGoldenDatasetIntegrity:
    """Verify the golden dataset itself is valid and well-formed."""

    def test_golden_dataset_exists(self):
        """Golden dataset file must exist."""
        assert GOLDEN_DATASET_PATH.exists(), (
            f"Golden dataset not found at {GOLDEN_DATASET_PATH}"
        )

    def test_golden_dataset_valid_json(self):
        """Golden dataset must be valid JSON."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "entries" in data

    def test_golden_dataset_has_entries(self):
        """Golden dataset must have at least 10 entries."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        assert len(data["entries"]) >= 10, (
            f"Expected >= 10 entries, got {len(data['entries'])}"
        )

    def test_golden_dataset_has_required_fields(self):
        """Every entry must have id, category, and expected fields."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        for entry in data["entries"]:
            assert "id" in entry, f"Entry missing 'id': {entry}"
            assert "category" in entry, (
                f"Entry {entry.get('id', '?')} missing 'category'"
            )
            assert "expected" in entry, f"Entry {entry['id']} missing 'expected'"

    def test_golden_dataset_categories_coverage(self):
        """Golden dataset must cover all required categories."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        categories = {e["category"] for e in data["entries"]}
        required = {"extraction", "qa", "deadline", "citation_integrity"}
        missing = required - categories
        assert not missing, f"Missing categories in golden dataset: {missing}"

    def test_golden_dataset_unique_ids(self):
        """All entry IDs must be unique."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        ids = [e["id"] for e in data["entries"]]
        assert len(ids) == len(set(ids)), "Duplicate entry IDs found"

    def test_golden_dataset_has_version(self):
        """Golden dataset must have a version field."""
        with open(GOLDEN_DATASET_PATH) as f:
            data = json.load(f)
        assert "version" in data, "Golden dataset missing 'version'"


# ---------------------------------------------------------------------------
# Core Metric Computation Tests
# ---------------------------------------------------------------------------


class TestCoreMetrics:
    """Tests for F1, precision, and recall computations."""

    def test_f1_perfect_match(self):
        assert compute_f1({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_f1_no_overlap(self):
        assert compute_f1({"x", "y"}, {"a", "b"}) == 0.0

    def test_f1_partial_overlap(self):
        result = compute_f1({"a", "b", "c"}, {"a", "b", "d"})
        assert 0.6 < result < 0.8  # F1 of 2/3 precision, 2/3 recall

    def test_f1_empty_sets(self):
        assert compute_f1(set(), set()) == 1.0

    def test_f1_empty_predicted(self):
        assert compute_f1(set(), {"a", "b"}) == 0.0

    def test_f1_empty_expected(self):
        assert compute_f1({"a"}, set()) == 0.0

    def test_precision_perfect(self):
        assert compute_precision({"a", "b"}, {"a", "b"}) == 1.0

    def test_precision_with_false_positives(self):
        assert compute_precision({"a", "b", "c"}, {"a"}) == pytest.approx(1 / 3)

    def test_recall_perfect(self):
        assert compute_recall({"a", "b"}, {"a", "b"}) == 1.0

    def test_recall_with_misses(self):
        assert compute_recall({"a"}, {"a", "b", "c"}) == pytest.approx(1 / 3)


# ---------------------------------------------------------------------------
# Citation Integrity Metric Tests
# ---------------------------------------------------------------------------


class TestCitationMetrics:
    """Tests for citation-specific metrics."""

    def test_citation_precision_all_valid(self):
        result = compute_citation_precision(
            ["doc-1", "doc-2"], {"doc-1", "doc-2", "doc-3"}
        )
        assert result == 1.0

    def test_citation_precision_with_fabricated(self):
        result = compute_citation_precision(["doc-1", "fake-doc"], {"doc-1", "doc-2"})
        assert result == 0.5

    def test_citation_precision_empty_citations(self):
        result = compute_citation_precision([], {"doc-1"})
        assert result == 1.0  # No citations is not fabrication

    def test_citation_recall_all_cited(self):
        result = compute_citation_recall(["doc-1", "doc-2"], {"doc-1", "doc-2"})
        assert result == 1.0

    def test_citation_recall_partial(self):
        result = compute_citation_recall(["doc-1"], {"doc-1", "doc-2"})
        assert result == 0.5

    def test_fabricated_citation_rate_clean(self):
        result = compute_fabricated_citation_rate(
            [{"document_id": "doc-1", "page_number": 1}],
            [{"id": "doc-1", "total_pages": 5}],
        )
        assert result == 0.0

    def test_fabricated_citation_rate_nonexistent_doc(self):
        result = compute_fabricated_citation_rate(
            [{"document_id": "fake-doc", "page_number": 1}],
            [{"id": "doc-1", "total_pages": 5}],
        )
        assert result == 1.0

    def test_fabricated_citation_rate_impossible_page(self):
        result = compute_fabricated_citation_rate(
            [{"document_id": "doc-1", "page_number": 15}],
            [{"id": "doc-1", "total_pages": 3}],
        )
        assert result == 1.0

    def test_cross_matter_contamination_clean(self):
        result = compute_cross_matter_contamination_rate(
            "Bu bir iş davası hakkındadır.", ["Ali Veli", "kira sözleşmesi"]
        )
        assert result == 0.0

    def test_cross_matter_contamination_detected(self):
        result = compute_cross_matter_contamination_rate(
            "Ali Veli'nin kira sözleşmesi incelendi.", ["Ali Veli", "kira sözleşmesi"]
        )
        assert result == 1.0


# ---------------------------------------------------------------------------
# Answer Quality Metric Tests
# ---------------------------------------------------------------------------


class TestAnswerQualityMetrics:
    """Tests for answer coverage and unsupported claim metrics."""

    def test_answer_coverage_full(self):
        coverage, missing = compute_answer_coverage(
            "Fatma Öztürk kıdem tazminatı ve fazla mesai talep etti.",
            ["Fatma Öztürk", "kıdem tazminatı", "fazla mesai"],
        )
        assert coverage == 1.0
        assert missing == []

    def test_answer_coverage_partial(self):
        coverage, missing = compute_answer_coverage(
            "Fatma Öztürk tazminat talep etti.",
            ["Fatma Öztürk", "kıdem tazminatı", "fazla mesai"],
        )
        assert 0.0 < coverage < 1.0
        assert len(missing) > 0

    def test_answer_coverage_with_forbidden_terms(self):
        coverage, _ = compute_answer_coverage(
            "Bu konuda bilgi bulunamadı. Ali dosyasından bilgi.",
            ["bulunamadı"],
            ["Ali dosyasından"],
        )
        # Coverage should be penalized due to must_not_contain violation
        assert coverage < 1.0

    def test_unsupported_claim_rate_all_supported(self):
        result = compute_unsupported_claim_rate(
            ["kıdem tazminatı ödenmemiştir"],
            ["İşçinin kıdem tazminatı ödenmediği tespit edilmiştir."],
        )
        assert result == 0.0

    def test_unsupported_claim_rate_unsupported(self):
        result = compute_unsupported_claim_rate(
            ["uzay mekiği fırlatıldı"], ["İş davası ile ilgili belgeler incelendi."]
        )
        assert result > 0.0


# ---------------------------------------------------------------------------
# Entity Extraction Metric Tests
# ---------------------------------------------------------------------------


class TestExtractionMetrics:
    """Tests for entity extraction F1 and role accuracy."""

    def test_entity_f1_exact_match(self):
        predicted = [{"name": "Mehmet Yılmaz"}, {"name": "ABC A.Ş."}]
        expected = [{"name": "Mehmet Yılmaz"}, {"name": "ABC A.Ş."}]
        assert compute_entity_extraction_f1(predicted, expected) == 1.0

    def test_entity_f1_fuzzy_match(self):
        """Fuzzy matching: 'ABC' should match 'ABC İnşaat A.Ş.' via containment."""
        predicted = [{"name": "ABC"}]
        expected = [{"name": "ABC İnşaat A.Ş."}]
        result = compute_entity_extraction_f1(predicted, expected)
        assert result > 0.0  # Should match via containment

    def test_entity_f1_no_match(self):
        predicted = [{"name": "Ahmet"}]
        expected = [{"name": "Mehmet"}]
        assert compute_entity_extraction_f1(predicted, expected) == 0.0

    def test_role_accuracy_correct(self):
        predicted = [
            {"name": "Mehmet", "role": "PLAINTIFF"},
            {"name": "ABC", "role": "DEFENDANT"},
        ]
        expected = [
            {"name": "Mehmet", "role": "PLAINTIFF"},
            {"name": "ABC", "role": "DEFENDANT"},
        ]
        assert compute_role_accuracy(predicted, expected) == 1.0

    def test_role_accuracy_wrong_role(self):
        predicted = [{"name": "Mehmet", "role": "DEFENDANT"}]
        expected = [{"name": "Mehmet", "role": "PLAINTIFF"}]
        assert compute_role_accuracy(predicted, expected) == 0.0


# ---------------------------------------------------------------------------
# Gate Evaluation Tests
# ---------------------------------------------------------------------------


class TestGateEvaluation:
    """Tests for quality gate evaluation logic."""

    def test_gate_pass(self):
        result = evaluate_gate("extraction_f1", 0.85, threshold=0.80)
        assert result.passed is True
        assert "PASS" in result.detail

    def test_gate_fail(self):
        result = evaluate_gate("extraction_f1", 0.70, threshold=0.80)
        assert result.passed is False
        assert "FAIL" in result.detail

    def test_gate_exact_threshold(self):
        result = evaluate_gate("extraction_f1", 0.80, threshold=0.80)
        assert result.passed is True

    def test_gate_inverse_metric_pass(self):
        """Inverse metrics (lower is better) should pass when score <= threshold."""
        result = evaluate_gate(
            "fabricated_citation_rate", 0.0, threshold=0.0, is_inverse=True
        )
        assert result.passed is True

    def test_gate_inverse_metric_fail(self):
        result = evaluate_gate(
            "fabricated_citation_rate", 0.05, threshold=0.0, is_inverse=True
        )
        assert result.passed is False

    def test_evaluation_report_all_passed(self):
        report = EvaluationReport()
        report.metrics.append(evaluate_gate("test_1", 0.90, threshold=0.80))
        report.metrics.append(evaluate_gate("test_2", 0.95, threshold=0.80))
        assert report.all_passed is True
        assert len(report.critical_failures) == 0

    def test_evaluation_report_with_failures(self):
        report = EvaluationReport()
        report.metrics.append(evaluate_gate("test_1", 0.90, threshold=0.80))
        report.metrics.append(evaluate_gate("test_2", 0.50, threshold=0.80))
        assert report.all_passed is False
        assert len(report.critical_failures) == 1

    def test_evaluation_report_summary(self):
        report = EvaluationReport()
        report.metrics.append(evaluate_gate("m1", 0.9, threshold=0.8))
        report.metrics.append(evaluate_gate("m2", 0.5, threshold=0.8))
        summary = report.summary()
        assert summary["total_metrics"] == 2
        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["all_passed"] is False
