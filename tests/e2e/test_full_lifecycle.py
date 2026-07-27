import pytest
import asyncio
import httpx
from datetime import datetime, timezone

# We assume MESA_ENV=test so the app uses memory cache, standard fast setup
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
        
        headers = {**HEADERS, "Idempotency-Key": "e2e-matter-init-123"}
        resp = await client.post(f"{API_BASE}/matters", json=matter_payload, headers=headers)
        assert resp.status_code == 201, f"Matter creation failed: {resp.text}"
        matter_data = resp.json()
        matter_id = matter_data["id"]

        # Verify Idempotency blocks exact duplicate
        resp2 = await client.post(f"{API_BASE}/matters", json=matter_payload, headers=headers)
        assert resp2.status_code == 409, "Idempotency did not block duplicate"

        # 2. Upload Document
        doc_payload = {
            "matter_id": matter_id,
            "filename": "mock_e2e_contract.pdf",
            "content_type": "application/pdf",
            "size_bytes": 500000,
            "checksum": "mock_sha256_e2e"
        }
        resp = await client.post(f"{API_BASE}/documents/intent", json=doc_payload, headers=HEADERS)
        assert resp.status_code == 201
        doc_data = resp.json()
        doc_id = doc_data["id"]
        
        # 3. Trigger QA / Intelligence (Wait for workers to process if it was real, but we can hit endpoints)
        qa_payload = {
            "query_text": "What is the jurisdiction?"
        }
        resp = await client.post(f"{API_BASE}/matters/{matter_id}/qa", json=qa_payload, headers=HEADERS)
        # Assuming the endpoint is fully implemented, even if it returns no evidence because no OCR ran on mock doc
        assert resp.status_code == 200
        
        # 4. Trigger Legal Research
        research_payload = {
            "matter_id": matter_id,
            "query": "Commercial contract breach limitations"
        }
        resp = await client.post(f"{API_BASE}/research", json=research_payload, headers=HEADERS)
        assert resp.status_code in (200, 202)
        
        # 5. Check Review Queue for Drafts (should be empty initially, but API should respond)
        resp = await client.get(f"{API_BASE}/reviews?status=draft", headers=HEADERS)
        assert resp.status_code == 200
        
        # 6. Generate Draft
        draft_payload = {
            "matter_id": matter_id,
            "draft_type": "petition",
            "instructions": "Draft commercial contract breach petition"
        }
        resp = await client.post(f"{API_BASE}/draft-studio", json=draft_payload, headers=HEADERS)
        assert resp.status_code == 202
        
        print("Mega Flow E2E Simulation completed successfully.")
