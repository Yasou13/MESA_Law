# MESA Law GDPR / KVKK Compliance Report

## 1. Overview
This document certifies that the Pilot Candidate architecture adheres to GDPR (Europe) and KVKK (Turkey) data protection regulations.

## 2. Key Compliance Pillars

### 2.1 Data Minimization
The AI parser only extracts predefined legal entities and claims. PII (Personal Identifiable Information) not strictly necessary for the legal case is not actively processed by the AI beyond standard OCR text extraction.

### 2.2 Security of Processing (Art. 32 GDPR)
- **Encryption in Transit**: TLS 1.3 enforced on all API endpoints. HSTS enabled.
- **Encryption at Rest**: AES-256 for PostgreSQL volumes and S3 buckets.
- **Access Control**: Strict RBAC and RLS guarantee isolation. Support staff uses `SUPPORT_TEMPORARY` break-glass accounts, generating permanent audit trails.

### 2.3 Data Portability & Erasure
Handled strictly according to `OFFBOARDING_RUNBOOK.md`.

### 2.4 AI and Automated Decision Making
MESA Law operates exclusively as an *assistive* tool. No automated decisions are made without human attorney intervention (`ATTORNEY_VERIFIED` constraint on all drafts and deadlines). Thus, it does not violate Article 22 of the GDPR regarding automated decision-making.
