# MESA Law Pilot Onboarding Runbook

## 1. Prerequisites
- Signed NDA and Data Processing Agreement (DPA) with the participating law firm.
- Initial list of participating attorneys and their roles (FIRM_ADMIN, ATTORNEY, PARALEGAL).
- Identified Pilot Champion from the firm.

## 2. Infrastructure Setup
1. Allocate tenant ID using UUID v4.
2. Verify Database Connection limits can accommodate the new firm (Scale up if required).
3. Setup firm's S3 Bucket namespace `/tenant_id/` to strictly partition storage.

## 3. Account Provisioning
1. Provide the Tenant ID and Initial Firm Details to the `setup_tenant.py` script.
2. The script provisions the firm in Keycloak:
   - Creates a dedicated group for the firm.
   - Sets up RBAC roles mapped to Keycloak client roles.
3. Users receive welcome emails to setup their MFA devices.

## 4. User Training & Guides
- Send `PILOT_USER_GUIDE.md` to all users.
- Send `PILOT_ADMIN_GUIDE.md` to the Firm Admin.

## 5. Day 1 Verification
- Firm Admin logs in and uploads 1 test PDF.
- Verify parsing completes and RAG returns verified citations.
- Confirm audit logs correctly attribute the action to the user and tenant.
