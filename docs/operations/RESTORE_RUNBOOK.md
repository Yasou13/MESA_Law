# MESA Law Restore Runbook

## 1. Prerequisites
- Access to the DR Kubernetes Cluster.
- Read-only access credentials to the Backup S3 Bucket.
- KMS Decryption keys for backup volumes.

## 2. Database Restore (PostgreSQL)
1. Provision a new PostgreSQL cluster (or use CloudNativePG CRD).
2. Configure `pgBackRest` or `WAL-G` with the backup bucket credentials.
3. Execute Point-in-Time Recovery (PITR):
   ```bash
   pgbackrest --stanza=mesa-db --type=time --target="2026-07-28 10:00:00" restore
   ```
4. Verify database state, ensure migrations table (`alembic_version`) matches the application version.

## 3. Object Storage Restore (MinIO/S3)
1. If using a secondary region replica, promote the replica bucket to primary.
2. Update application ConfigMaps to point to the new bucket endpoint.
3. Validate document hash integrity against the restored PostgreSQL database using the `verify_hashes.py` script.

## 4. Keycloak Restore
1. Deploy Keycloak.
2. Import the latest realm JSON export:
   ```bash
   /opt/keycloak/bin/kc.sh import --file /tmp/realm-export.json
   ```

## 5. Application Spin-Up & Validation
1. Deploy MESA Law FastAPI and Next.js applications pointing to the restored DB and Storage.
2. Execute Smoke Tests:
   - Login as `FIRM_ADMIN`.
   - Access a matter.
   - Verify document viewing and citation resolution.
   - Confirm audit records exist up to the PITR target.
