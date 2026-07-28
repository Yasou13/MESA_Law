# MESA Law - Legal AI Evaluation Framework

## 1. Overview
The MESA Law AI Evaluation Framework ensures that language models deployed for legal extraction, Q&A, and citation generation meet rigorous accuracy and safety standards. This framework builds upon the MESA v0.3.0 Ground Truth schema but is tailored explicitly for legal domain challenges.

## 2. Benchmark Data Categories
The benchmark suite is partitioned into the following test categories:
- **Taraf Çıkarımı (Party Extraction)**
- **Olay Çıkarımı (Event Extraction)**
- **İddia ve Savunma Çıkarımı (Claim & Defense Extraction)**
- **Delil İlişkilendirme (Evidence Linking)**
- **Citation Doğruluğu (Citation Accuracy)**
- **Timeline Sıralaması (Chronological Ordering)**
- **Deadline Trigger Tespiti (Deadline Detection)**
- **Source-Grounded Q&A (RAG QA)**
- **Contradiction Detection (Conflict Checking)**
- **Legal Research Retrieval**

## 3. Ground Truth Schema
Each benchmark example in the Golden Dataset contains:
- `input_document`: The raw source text.
- `expected_structured_output`: The exact JSON or text schema expected.
- `allowed_variation`: Semantic similarity threshold (using cosine similarity on embeddings) for text answers.
- `required_citations`: Strict list of SourceLocator IDs that MUST be cited.
- `forbidden_claims`: Claims that the model MUST NOT make (to test hallucination).
- `review_notes`: Context for the human reviewer if manual sampling is triggered.

## 4. Evaluation Metrics
We measure the following KPIs across the benchmark dataset:
- **Precision / Recall / F1 Score**: For entity and event extraction.
- **Citation Precision**: % of generated citations that accurately point to the expected source snippet.
- **Citation Recall**: % of expected citations that were successfully generated.
- **Unsupported Claim Rate**: % of claims generated without a verified source (Target: 0%).
- **Fabricated Citation Rate**: % of citations pointing to non-existent sources (Target: 0%).
- **Cross-Matter Contamination Rate**: % of answers blending facts from distinct test matters (Target: 0%).
- **Deadline False-Positive / False-Negative Rate**: Errors in trigger date identification (Target FP: 0%, FN: <2%).

## 5. Execution
The evaluation is executed via `evaluation/eval_runner.py`. The pipeline compares model outputs against `tests/data/golden_dataset.json`. A model cannot be promoted to `APPROVED` or `PILOT_CANARY` if it fails any of the strict Target: 0% gates.
