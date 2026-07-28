# MESA Law RBAC Verification Report

## 1. Overview
This report verifies that the Role-Based Access Control (RBAC) model implemented via `apps.api.core.policies` correctly enforces access across all tenant contexts and roles.

## 2. Supported Roles
- **FIRM_ADMIN**: Full access within the firm. Can rebuild MESA, elevate roles, override conflicts.
- **ATTORNEY**: Can create matters, upload documents, approve drafts for external use, override conflicts.
- **PARALEGAL**: Can upload documents, edit drafts, but CANNOT approve drafts for external use or override conflicts.
- **READ_ONLY**: Can view matters and documents but cannot create, update, or approve anything.
- **AUDITOR**: Can access audit endpoints and view matters.
- **SUPPORT_TEMPORARY**: Break-glass role. Has read-only access to specifically approved matters.

## 3. Negative Test Matrix Results
Automated negative tests (`test_role_permission_matrix.py`) assert that any action performed by an unauthorized role results strictly in an `HTTP 403 Forbidden` response and triggers no data modification.

| Endpoint | Action | Allowed Roles | Blocked Roles (HTTP 403) |
|---|---|---|---|
| `POST /matters` | Create Matter | FIRM_ADMIN, ATTORNEY | PARALEGAL, READ_ONLY, AUDITOR, SUPPORT |
| `POST /matters/{id}/rebuild-mesa` | Rebuild Index | FIRM_ADMIN | ATTORNEY, PARALEGAL, READ_ONLY, AUDITOR |
| `POST /matters/{id}/override-conflict` | Override Conflict | FIRM_ADMIN, ATTORNEY | PARALEGAL, READ_ONLY, AUDITOR, SUPPORT |
| `POST /documents` | Upload Doc | FIRM_ADMIN, ATTORNEY, PARALEGAL | READ_ONLY, AUDITOR, SUPPORT |
| `POST /drafts/{id}/approve` | Approve External | FIRM_ADMIN, ATTORNEY | PARALEGAL, READ_ONLY, AUDITOR, SUPPORT |
| `PUT /firms/{id}/members/{uid}/role` | Elevate Role | FIRM_ADMIN | ATTORNEY, PARALEGAL, READ_ONLY, AUDITOR |

## 4. Audit & Verification
All access denials are captured by the error handlers and the API logs. The database level (`RLS`) provides a secondary boundary ensuring that even if a role check is bypassed, the user cannot access out-of-tenant data.

**STATUS**: PASS
**DATE**: 2026-07-28
