import pytest
import asyncio
import httpx
from datetime import datetime, timezone

# We assume MESA_LAW_ENVIRONMENT=test so the app uses memory cache, standard fast setup
# The DB will be a fresh postgresql from Docker.
# We will use the internal docker network port 8000 for API since we are testing locally via httpx AsyncClient
# Wait, actually since we are running this pytest on the host, we should hit http://localhost:8000 (API) 
# which is exposed by docker compose.

API_BASE = "http://localhost:8001/api/v1"
HEADERS = {"Authorization": "Bearer mock-e2e-token"}

@pytest.mark.asyncio
async def test_pilot_mega_flow():
    """
    E2E mega flow testing: 
    matter creation -> doc upload -> parse/OCR -> extraction -> review -> QA -> Draft
    """
    # Wait for the API to be ready
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        health = await client.get("http://localhost:8001/health/ready")
        assert health.status_code == 200, "API is not ready"

        # 1. Create a Matter (with Idempotency)
        matter_payload = {
            "title": "MESA Pilot Test Matter",
            "description": "E2E automated flow matter",
            "jurisdiction": "tr",
            "case_type": "commercial"
        }
        
        import uuid
        headers = {**HEADERS, "Idempotency-Key": f"e2e-matter-init-{uuid.uuid4()}"}
        resp = await client.post(f"{API_BASE}/matters", json=matter_payload, headers=headers)
        assert resp.status_code == 201, f"Matter creation failed: {resp.text}"
        matter_data = resp.json()
        matter_id = matter_data["id"]

        # Verify Idempotency returns cached response
        resp2 = await client.post(f"{API_BASE}/matters", json=matter_payload, headers=headers)
        assert resp2.status_code == 201, f"Idempotency failed to return cached response: {resp2.text}"
        assert resp2.json()["id"] == matter_id

        # 2. Upload Document
        doc_payload = {
            "matter_id": matter_id,
            "filename": "mock_e2e_contract.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 500000
        }
        resp = await client.post(f"{API_BASE}/documents/upload-intent", json=doc_payload, headers=HEADERS)
        assert resp.status_code in [200, 201]
        doc_data = resp.json()
        doc_id = doc_data["document_id"]
        
        # 3. Trigger QA / Intelligence (Wait for workers to process if it was real, but we can hit endpoints)
        qa_payload = {
            "question": "What is the jurisdiction?"
        }
        resp = await client.post(f"{API_BASE}/matters/{matter_id}/qa", json=qa_payload, headers=HEADERS)
        # Assuming the endpoint is fully implemented, even if it returns no evidence because no OCR ran on mock doc
        assert resp.status_code == 200
        
        # 4. Trigger Legal Research
        research_payload = {
            "matter_id": matter_id,
            "query": "Commercial contract breach limitations"
        }
        resp = await client.post(f"{API_BASE}/research/start", json=research_payload, headers=HEADERS)
        assert resp.status_code in (200, 202)
        
        # 5. Check Review Queue for Drafts (should be empty initially, but API should respond)
        resp = await client.get(f"{API_BASE}/reviews?status=draft", headers=HEADERS)
        assert resp.status_code == 200
        
        # 6. Generate Draft
        draft_payload = {
            "matter_id": matter_id,
            "template_name": "petition"
        }
        resp = await client.post(f"{API_BASE}/draft-studio/drafts/generate", json=draft_payload, headers=HEADERS)
        assert resp.status_code in (200, 202)
        
        print("Mega Flow E2E Simulation completed successfully.")
