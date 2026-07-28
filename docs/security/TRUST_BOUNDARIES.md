# MESA Law Trust Boundaries

This document maps out the logical and physical trust boundaries within the MESA Law infrastructure, determining where authentication and validation must occur as data crosses zones.

## 1. External Untrusted Zone
- **Entities**: End-user Browsers (Attorneys, Paralegals, Clients).
- **Boundary Control**: The boundary is protected by the Reverse Proxy (Ingress) and Next.js frontend, which handle initial TLS termination and basic request filtering.

## 2. Authentication Boundary (Keycloak)
- **Entities**: Keycloak Identity Provider (IdP).
- **Boundary Control**: Only valid, signed JWTs (access tokens) are accepted by the FastAPI backend. Keycloak manages JWKS rotation, session lifecycle, and OIDC flows. The application strictly validates audience and issuer.

## 3. API Application Boundary (FastAPI)
- **Entities**: FastAPI Backend Application.
- **Boundary Control**: This is the primary enforcement point for RBAC and business logic. It establishes the `tenant_id` context and restricts external input. Data crossing from the API to internal services must be sanitized.

## 4. Database Security Boundary (PostgreSQL)
- **Entities**: PostgreSQL Database.
- **Boundary Control**: Row-Level Security (RLS) is the ultimate backstop. The API communicates with the DB using non-superuser roles (`mesa_law_app`). The database explicitly rejects operations outside the defined `app.current_tenant` context.

## 5. Storage Boundary (MinIO/S3)
- **Entities**: Object Storage.
- **Boundary Control**: Direct access to storage is denied. The API issues short-lived, permission-checked presigned URLs for client uploads and downloads.

## 6. Asynchronous Worker Boundary (Celery/Redis)
- **Entities**: Background Workers, OCR/Parser Jobs, ClamAV.
- **Boundary Control**: Workers consume jobs from Redis. Job payloads must carry the authenticated `tenant_id` to ensure isolated processing. Workers operate with the `mesa_law_worker` DB role.

## 7. External Intelligence Providers Boundary
- **Entities**: External Model Providers (OpenAI, Anthropic), Legal Source Providers (Legislation APIs).
- **Boundary Control**: MESA Law interacts with external models by passing sanitized text (data) and strict system prompts. Customer data is strictly segregated and excluded from model training loops. MESA Core connections are authenticated via dedicated credentials.
