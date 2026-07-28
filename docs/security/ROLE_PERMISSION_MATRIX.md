# MESA Law - Role Permission Matrix

This matrix describes the authoritative permissions for roles mapped within the MESA Law platform as defined in Phase 1 of the Controlled Pilot transition.
All roles are enforced via robust `*AccessPolicy` dependencies evaluated during each request.

| Action | FIRM_ADMIN | ATTORNEY | PARALEGAL | READ_ONLY | AUDITOR | SUPPORT_TEMPORARY |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Matters** | | | | | | |
| Read Matters | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Create Matters | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Matter Members | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Close Matters | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | |
| **Documents** | | | | | | |
| Read Documents | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Upload Documents | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| | | | | | | |
| **Reviews (AI Suggestions)** | | | | | | |
| Approve/Reject/Correct | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | |
| **Draft Studio** | | | | | | |
| Create/Update Drafts | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Export Drafts | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Approve for External Use | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | |
| **Deadlines** | | | | | | |
| Manage Candidates | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Verify/Approve Deadlines | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| | | | | | | |
| **System/Admin** | | | | | | |
| Rebuild MESA Index | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage Firm Members | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| View Audit Logs | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Advanced Support Actions | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### Policy Definitions
- **MatterAccessPolicy**: Enforces read, create, member management, and closure controls for matters.
- **DocumentAccessPolicy**: Enforces read and upload controls for matter documents.
- **ReviewAccessPolicy**: Protects the final approval and canonical publishing pipeline for ReviewItems.
- **DraftAccessPolicy**: Manages who can generate drafts and critically limits who can sign-off drafts for external distribution.
- **ExportAccessPolicy**: Authorizes document exports (PDF/Word).
- **DeadlineAccessPolicy**: Determines who can create candidates vs. who can definitively verify them on the calendar.
- **AdminAccessPolicy**: Protects tenant-wide settings, user memberships, and MESA system rebuilds.
- **SupportAccessPolicy**: Reserved strictly for the `SUPPORT_TEMPORARY` role.
