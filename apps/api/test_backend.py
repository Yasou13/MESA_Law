import pytest
from apps.api.core.database import AsyncSessionLocal, get_db
from apps.api.core.errors import (
    ProblemException,
    global_exception_handler,
    problem_exception_handler,
)
from apps.api.core.idempotency import check_idempotency, complete_idempotency
from apps.api.core.middleware import TraceMiddleware
from fastapi import Depends, FastAPI, Header
from fastapi.testclient import TestClient

app = FastAPI()
app.add_middleware(TraceMiddleware)
app.add_exception_handler(ProblemException, problem_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.post("/test-idempotency")
async def mock_endpoint(idem_key: str = Header(...), db = Depends(get_db)):
    # Check
    cached = await check_idempotency(db, idem_key)
    if cached:
        return cached.response_body
        
    # Simulate work
    resp = {"result": "success"}
    await complete_idempotency(db, idem_key, 200, resp)
    return resp

@app.get("/test-error")
async def error_endpoint():
    raise ProblemException(400, "Bad Request", "This is a test error")

client = TestClient(app)

@pytest.mark.asyncio
async def test_problem_json_handler():
    response = client.get("/test-error")
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    data = response.json()
    assert data["title"] == "Bad Request"
    assert data["detail"] == "This is a test error"

@pytest.mark.asyncio
async def test_idempotency():
    import uuid6
    test_key = str(uuid6.uuid7())
    
    # First request
    response1 = client.post("/test-idempotency", headers={"idem-key": test_key})
    assert response1.status_code == 200
    assert response1.json() == {"result": "success"}
    
    # Second request with same key
    response2 = client.post("/test-idempotency", headers={"idem-key": test_key})
    assert response2.status_code == 200
    assert response2.json() == {"result": "success"}
    
    # Test Conflict (simulating in_progress)
    async with AsyncSessionLocal() as db:
        test_key2 = str(uuid6.uuid7())
        await check_idempotency(db, test_key2) # sets it to in_progress
        
    response3 = client.post("/test-idempotency", headers={"idem-key": test_key2})
    assert response3.status_code == 409
    data = response3.json()
    assert data["title"] == "Conflict"
