# Work Order 014 (WO-014) Handoff - Gap Analysis

## Objective
Analyze the gap between MESA-Law's current mock intelligence requirements (Evre A) and the actual capabilities of the MESA core framework (`Desktop/MESA`), establishing the roadmap for Evre B (MESA Adaptation).

## Capability Mapping & Classification

### 1. Document Ingestion & Parsing
**Requirement:** Parse Turkish legal documents (PDF/Word), perform OCR, and extract text/tables.
**MESA Core Status:** MESA provides standard document ingestion, but specialized Turkish OCR and legal structural parsing (differentiating "Esas No", "Karar No") is likely not native.
**Classification:** `WORKAROUND` (MESA-Law will need a pre-processing adapter before sending raw text to MESA).

### 2. Timeline & Chronological Events
**Requirement:** Extract chronological events, tie them to specific citations, and visualize them.
**MESA Core Status:** MESA's Memory/Graph engine supports extracting events and temporal relations. However, custom properties specific to Turkish law (e.g. "İhtarname", "Fesih") might require domain specific prompts.
**Classification:** `SUPPORTED` (Requires custom schema definitions passed to MESA).

### 3. Claims & Evidence (Assertions)
**Requirement:** Identify legal claims, assign confidence scores, and link supporting/refuting evidence.
**MESA Core Status:** MESA's assertion engine supports node-edge graphs (e.g. `[Claim] -> SupportedBy -> [Evidence]`).
**Classification:** `SUPPORTED` (The graph memory is a perfect fit).

### 4. Legal Research & Q&A
**Requirement:** Query normalized current/historical legislation and case law.
**MESA Core Status:** MESA has retrieval capabilities, but it expects generic vector/RAG indices. The specialized "Golden Legal Package" (WO-012) validation and search over historical normalization requires an adapter.
**Classification:** `WORKAROUND` (We must build a specialized Legal Search tool that MESA agents can call via MCP or direct function calling).

### 5. Multi-Tenant Isolation
**Requirement:** Strict isolation of data between different law firms (`tenant_id`).
**MESA Core Status:** MESA might lack strict multi-tenant RLS built-in natively depending on its setup (usually meant for single-user/single-system memory).
**Classification:** `CORE_CHANGE` or `WORKAROUND` (MESA-Law must proxy all requests and inject tenant isolation, or MESA needs an upgrade).

## Action Plan for Evre B
1. **Adapter Layer**: Build `apps/api/core/mesa_adapter.py` to translate MESA-Law models (WO-006, WO-010) into MESA graph operations.
2. **Custom Prompts**: Define Turkish legal prompts/schemas to feed into MESA's extraction engine.
3. **Tenant Proxy**: Implement strict routing where MESA-Law validates `tenant_id` and `matter_id` before invoking MESA memory reads/writes.
4. **Contract Tests**: Write `tests/test_mesa_contracts.py` to verify MESA behaves as expected when given these legal schemas.

## Next Suggested Work Order
- **Evre B** implementation (Starting the real MESA integration based on this adapter layer).
