"""Running-stack Law API contract; requires the explicit integration profile."""

import uuid

import httpx
import pytest

API_ROOT = "http://localhost:8001"
API_BASE = f"{API_ROOT}/api/v1"
HEADERS = {"Authorization": "Bearer dev-mock-token"}


@pytest.mark.asyncio
async def test_law_stack_mvp_contract() -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            health = await client.get(f"{API_ROOT}/health/ready")
        except httpx.ConnectError:
            pytest.fail("Law integration API is not running on localhost:8001")
        assert health.status_code == 200, health.text

        idempotency_key = f"law-e2e-matter-{uuid.uuid4()}"
        matter_payload = {
            "title": "MESA Law integration matter",
            "jurisdiction": "TR",
            "case_type": "commercial",
        }
        headers = {**HEADERS, "Idempotency-Key": idempotency_key}
        matter_response = await client.post(
            f"{API_BASE}/matters", json=matter_payload, headers=headers
        )
        assert matter_response.status_code == 201, matter_response.text
        matter = matter_response.json()

        duplicate = await client.post(
            f"{API_BASE}/matters", json=matter_payload, headers=headers
        )
        assert duplicate.status_code == 201, duplicate.text
        assert duplicate.json()["id"] == matter["id"]

        upload = await client.post(
            f"{API_BASE}/documents/upload-intent",
            json={
                "matter_id": matter["id"],
                "filename": "contract.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
            },
            headers=HEADERS,
        )
        assert upload.status_code == 200, upload.text
        assert upload.json()["storage_key"].startswith("quarantine/")

        qa = await client.post(
            f"{API_BASE}/qa/ask",
            json={
                "matter_id": matter["id"],
                "question": "What verified evidence is available?",
            },
            headers=HEADERS,
        )
        assert qa.status_code == 200, qa.text
        assert qa.json()["status"] == "ABSTAIN"
        assert qa.json()["citations"] == []

        research = await client.post(
            f"{API_BASE}/research/start",
            json={"matter_id": matter["id"], "query": "contract breach"},
            headers=HEADERS,
        )
        assert research.status_code == 501

        draft = await client.post(
            f"{API_BASE}/draft-studio/drafts/generate",
            json={"matter_id": matter["id"], "template_name": "petition"},
            headers=HEADERS,
        )
        assert draft.status_code == 501

        rebuild = await client.post(
            f"{API_BASE}/matters/{matter['id']}/rebuild-mesa", headers=HEADERS
        )
        assert rebuild.status_code == 501
