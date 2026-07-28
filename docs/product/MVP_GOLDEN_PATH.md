# MESA Law MVP Golden Path

The Golden Path represents the single critical flow that must work reliably end-to-end for the MVP to be considered successful.

## Execution Flow

1. **Identity**: User logs in via Keycloak and enters their Active Firm context securely.
2. **Setup**: User creates a new Matter and assigns appropriate user roles.
3. **Ingestion**: User uploads a legal document (PDF/DOCX). System successfully scans (ClamAV), parses (PyMuPDF/OCR), and transitions to `READY`.
4. **Extraction**: Worker pipeline extracts `PARTY`, `EVENT`, `CLAIM`, and `EVIDENCE` intelligence.
5. **Review**: Paralegal or Attorney accesses Review Center, edits/corrects a suggestion, and approves it.
6. **Publication**: The Canonical Publisher synchronously updates the core PostgreSQL database, generating an Audit Event.
7. **Exploration**: User navigates to the Matter details and queries the AI (Matter Q&A) for insights. AI responds with a verified citation linked to a true `SourceLocator`.
8. **Drafting**: User drafts a response in Draft Studio utilizing the retrieved intelligence.
9. **Approval**: An Attorney approves the Draft for external use.
10. **Delivery**: The Draft is successfully exported to PDF/DOCX for download.

*Failure at any point in this flow invalidates the MVP.*
