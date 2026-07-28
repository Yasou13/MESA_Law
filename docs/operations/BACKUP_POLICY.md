# MESA Law Backup Policy

## 1. Objectives
- **RPO (Recovery Point Objective)**: ≤ 15 minutes.
- **RTO (Recovery Time Objective)**: ≤ 4 hours.

## 2. Scope of Backups
1. **PostgreSQL Database**: All tenant data, audit logs, matter records, and rule configurations.
2. **Object Storage (MinIO/S3)**: Original PDF/DOCX documents, legal source snapshots, and export artifacts.
3. **Keycloak Configuration**: Realm exports, client definitions, and user state.
4. **Application Secrets Metadata**: Encrypted definitions of external secrets (Vault / External Secrets Operator).

## 3. Backup Schedule & Strategy
### 3.1 Database
- **Continuous Archiving (WAL)**: WAL logs shipped every 5 minutes to S3 (pgBackRest/WAL-G) ensuring < 15 min RPO.
- **Full Backups**: Weekly full snapshots.
- **Incremental Backups**: Daily incremental snapshots.

### 3.2 Object Storage
- **Versioning**: Enabled on all S3 buckets to protect against accidental overrides or ransomware.
- **Cross-Region Replication**: Asynchronous replication to a secondary geographical region.

### 3.3 Keycloak
- Daily automated realm exports stored securely in S3.

## 4. Security & Retention
- **Encryption**: All backups are encrypted at rest (AES-256) with CMK (Customer Managed Keys).
- **Isolation**: Backup storage credentials are write-only from production and strictly read-only for the DR environment.
- **Retention**: Daily backups kept for 30 days. Weekly for 12 weeks. Monthly for 10 years (critical legal audit requirement). Legal hold propagation ensures backups containing legal hold data are not purged prematurely.
