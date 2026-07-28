# MESA Law MVP Scope

## 1. Goal
Deliver a working, reliable, and secure single-path "Controlled Pilot Candidate" MVP.

## 2. In-Scope Features (MVP)

### Authentication & Tenant
- Keycloak login and token validation
- Server-side active firm isolation
- Role-based permissions (FIRM_ADMIN, ATTORNEY, PARALEGAL, READ_ONLY)

### Matter Management
- Create, list, update, and close matters
- Matter-specific access control (MatterMember)

### Document Pipeline
- Secure upload (PDF, DOCX, TXT) with ClamAV integration
- Robust document parsing and OCR (graceful fallback)
- SourceLocator linkage generation

### Review Center
- AI Extraction limited to: PARTY, EVENT, CLAIM, EVIDENCE
- Human-in-the-loop review (Approve, Edit & Approve, Reject)
- Single Canonical Publisher (idempotent writes to domain DB)

### Operations & Output
- Matter-scoped Q&A (verified citations only)
- Draft Studio (Create, edit, approve for external use)
- Export to PDF and DOCX
- Synchronized audit logging for major events

## 3. Excluded
Everything listed in `MVP_OUT_OF_SCOPE.md` is strictly excluded to protect the Golden Path.
