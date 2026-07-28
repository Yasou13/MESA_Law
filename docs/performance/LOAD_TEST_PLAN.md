# MESA Law Load Test Plan

## 1. Objectives
- Ensure the API handles 10, 25, and 50 concurrent active users.
- Verify that standard endpoints respond within < 800ms at the P95 percentile.
- Verify `GET /api/v1/matters` responds within < 3 seconds at P95 under heavy load.
- Ensure the worker queue efficiently processes large document uploads without OOM errors.

## 2. Test Profiles
1. **Light Load**: 10 Concurrent Users. 1 uploaded document/min. Normal review/RAG operations.
2. **Target Load**: 25 Concurrent Users. 5 documents/min. High volume of Draft auto-saves and Review operations.
3. **Stress Load**: 50 Concurrent Users. Peak document parsing load to identify worker bottlenecks and DB connection exhaustion.

## 3. Tooling
- We use **Locust** and **k6** for simulating API interactions and Keycloak authentication.

## 4. Key Metrics Monitored
- `app.http.response_time` (API Latency)
- `db.pool.active_connections` (Connection Pool saturation)
- `celery.queue.latency` (Background Job Wait Time)
- `worker.memory.usage` (RAM limits, especially for PyMuPDF)
