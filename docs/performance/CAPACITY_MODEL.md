# MESA Law Capacity Model

## 1. Baseline Pilot Constraints
For the controlled pilot (2-3 law firms, up to 20 attorneys each), the system is explicitly bound by the following hard limits to ensure stability:

| Resource | Soft Limit | Hard Limit | Enforcement Point |
|---|---|---|---|
| Max Document Size | 100 MB | 250 MB | FastAPI Upload Router |
| Max Document Pages | 1000 | 2500 | `parser_worker.py` |
| Max Pages per Matter | 20,000 | 50,000 | `upload` (pre-calc query) |
| Max Concurrent Parses | 5 | 10 | Celery Concurrency |
| Max Uploads / Min | 10 | 30 | Redis Rate Limiter |

## 2. Compute Allocation (Kubernetes)
- **API Pods**: 2 Replicas. Limits: 1 CPU, 1Gi RAM.
- **Worker Pods (Parser/OCR)**: 3-5 Replicas (HPA). Limits: 2 CPU, 4Gi RAM.
- **PostgreSQL**: 4 vCPU, 16Gi RAM.
- **MinIO**: Minimum 500GB NVMe storage.

## 3. Expected Costs
- **LLM Token Costs**: Assuming average 10K context per Q&A, ~1M tokens / firm / month = ~$10-30/month (Anthropic/OpenAI tier dependent).
- **Storage**: ~50GB / firm / year.
- **Total Compute**: ~$300/month on standard cloud instances.
