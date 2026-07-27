# Work Order Handoff

## Completed Work
1. **Security & Config**: Updated config.py for secure environments, added CSP and CSRF middleware in main.py, refactored pilot-deployment.yaml.
2. **Networking**: Fixed Keycloak Docker network links for the API.
3. **Dependencies & Export**: Added pyproject.toml dependencies (pytesseract, reportlab, python-docx), updated worker.Dockerfile for OCR, and fixed export.py to output actual PDF and DOCX formats.
4. **Domain & DB Models**: Created models for `MatterEvent`, `ClaimEvidenceLink`, `ReviewItem`, and `DraftRevision`. Written manual alembic migration.
5. **Routers (Intelligence)**: Updated QA and Research routers for auth, proper logic structure and AI citation coverage.
6. **Tests & CI**: Implemented real postgres-based RLS tests, and created comprehensive GitHub Actions ci.yml pipeline.

1. **CSRF & Networking**: Removed global CSRF for API, updated `axios` and `providers` to use dynamic env URLs, and added `wellKnown` to KeycloakProvider for NextAuth internal discovery.
2. **Mock Kısıtlamaları & OCR**: `settings.env == "production"` yerine `settings.is_secure_environment` kullanıldı. OCR başarısızlığında dummy text üretmesi engellendi.
3. **Extraction Review Flow**: Heuristic/AI extraction sonuçları doğrudan `MatterParty` veya `Claim` olmak yerine, `ReviewItem` tablosuna JSON formatında kaydedilecek şekilde düzeltildi.
4. **CI & Test Enforcements**: CI pipeline'ında Playwright başarısızlığını saklayan `|| echo` kapatıldı ve typecheck eklendi. RLS testleri `mesa_law_app` application role'u kullanılarak non-superuser modunda test edilmeye başlandı.

## Pending Items
- E2E Playwright testlerinin baştan sona eksiksiz yazılması.
- Q&A modülünde Türkçe Full Text Search ve doküman snapshot skorlamasının entegrasyonu.
