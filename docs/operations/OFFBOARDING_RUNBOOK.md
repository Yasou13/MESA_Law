# MESA Law Offboarding & Data Portability Runbook

## 1. Trigger
Pilot concludes without a commercial agreement, or firm requests account termination.

## 2. Execution Strategy
MESA Law complies with GDPR/KVKK Right to Erasure and Data Portability.

### 2.1 Export Phase (Data Portability)
1. Run the `export_tenant_data.py` script with the target `tenant_id`.
2. This generates a secure, encrypted ZIP file containing:
   - All original documents (PDF/DOCX).
   - Structured JSON export of all Matters, Drafts, and Approved ReviewItems.
   - Audit trail JSON for compliance.
3. Provide the download link to the FIRM_ADMIN via a secure, time-limited Presigned URL.

### 2.2 Purge Phase (Right to Erasure)
1. Delete Keycloak Group and Users for the tenant.
2. Execute the DB hard purge script:
   ```bash
   python scripts/purge_tenant.py --tenant-id UUID --confirm
   ```
3. Empty and delete the S3 namespace for the tenant.
4. Note: Data in automated backups will expire organically after the 30-day retention period. Manual deletion from backup snapshots is computationally infeasible and exempt under standard GDPR practices as long as it's not restored to production.
