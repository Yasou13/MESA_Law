# MESA Law Threat Model (STRIDE Methodology)

## 1. Introduction
This document defines the threat model for the MESA Law platform based on the STRIDE methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). It outlines the primary threats associated with the application's architecture and the controls in place to mitigate them.

## 2. Assumed Assets
The system protects the following critical assets:
- OIDC session & JWTs
- Tenant context and firm boundaries
- Matter metadata and associated documents
- Original documents and OCR outputs
- Canonical legal data and Drafts
- Deadline records
- Legal source packages
- Audit records
- MESA projections
- Backup files
- Support access credentials

## 3. Threat Analysis (STRIDE)

### 3.1 Spoofing Identity
- **Threat**: Attackers could forge a JWT or exploit session fixation to impersonate a legitimate user or FIRM_ADMIN.
- **Threat**: JWT Confusion attacks (e.g., changing algorithm to 'none' or 'HS256' with public key).
- **Mitigations**: 
  - Strict validation of `issuer`, `audience`, and `signature`.
  - Enforced `HttpOnly`, `Secure`, and `SameSite` flags on session cookies.
  - Recent authentication requirements for critical actions (e.g., external-use export, role elevation).

### 3.2 Tampering with Data
- **Threat**: Citation forgery by manipulating AI-generated text or referencing non-existent SourceLocators.
- **Threat**: Deadline manipulation (e.g., injecting false trigger dates or skipping verified rules).
- **Threat**: Audit tampering by support accounts.
- **Mitigations**:
  - Deterministic SourceLocator mapping and strict citation verification pipelines (STALE_REVISION, SOURCE_MISSING).
  - Append-only audit logs with immutability guarantees.
  - Role-Based Access Control (RBAC) preventing unauthorized modifications.

### 3.3 Repudiation
- **Threat**: Users denying taking destructive actions (e.g., deleting matters, overriding conflict checks).
- **Mitigations**:
  - Comprehensive append-only audit trails linked to deterministic `principal_id` and `trace_id`.
  - Non-deletable log structures ensuring full accountability.

### 3.4 Information Disclosure
- **Threat**: Cross-tenant data leakage via direct object reference (BOLA/IDOR).
- **Threat**: Unauthorized access to backup files or MESA indices.
- **Threat**: System prompt disclosure via prompt injection attacks.
- **Mitigations**:
  - Strict Row-Level Security (RLS) bound to `app.current_tenant`.
  - Validated presigned URLs with short expirations for object storage.
  - Instruction boundaries for AI to prevent prompt leakage.

### 3.5 Denial of Service (DoS)
- **Threat**: Malicious document uploads (e.g., ZIP bombs, malformed PDFs) consuming worker memory.
- **Threat**: Excessive complex legal research queries saturating the database or LLM provider.
- **Mitigations**:
  - Rate limiting via Redis.
  - ClamAV scanning and strict file size/page limits (max 250MB / 2500 pages per file).
  - Worker timeout controls and decoupled asynchronous queues.

### 3.6 Elevation of Privilege
- **Threat**: Users escalating roles (e.g., PARALEGAL to FIRM_ADMIN).
- **Threat**: Exploiting Support accounts for persistent access.
- **Threat**: SSRF (Server-Side Request Forgery) via malicious inputs to external legal sources.
- **Mitigations**:
  - Explicit backend enforcement via `BasePolicy._enforce`.
  - Time-bound, read-only defaults for Support access (break-glass protocols).
