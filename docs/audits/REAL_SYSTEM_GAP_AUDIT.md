# MESA Law - Real System Gap Audit

## Modül Statüleri

Aşağıdaki modüller mevcut repository'nin mevcut durumuna göre incelenmiş ve kategorize edilmiştir.

| Modül | Durum | Gözlemler |
|-------|-------|-----------|
| **Deployment & Local Stack** | `SCAFFOLDED` | Docker Compose mevcut ama Keycloak/bootstrap, Caddy, OTel vb. eksik. K8s pilot yaml boş. |
| **Authentication** | `SCAFFOLDED` | `mock-user-id` sabit olarak üretiliyor. Frontend'de `localStorage`'dan tenant id alınıyor. |
| **Authorization (RBAC & Policy)** | `NOT_STARTED` | Kapsamlı yetki modeli yok. Matter bazlı ve Role bazlı (FIRM_ADMIN, vb.) yetkilendirme eksik. |
| **PostgreSQL RLS & Tenant İzolasyonu** | `SCAFFOLDED` | ORM seviyesinde SQLAlchemy guard var, ancak gerçek Postgres RLS politikaları (ENABLE ROW LEVEL SECURITY) yok. |
| **Document Ingestion & Upload** | `SCAFFOLDED` | Yalnız presigned URL var. Hash, ClamAV, MIME validation, finalize endpoint'i yok. Karantina akışı eksik. |
| **Worker & Durable Jobs** | `SCAFFOLDED` | Queue sınıfı var ancak gerçek worker entrypoint, job handler registry (scan, parse, ocr vb.) ve loop mekanizması yok. |
| **Parser & OCR Pipeline** | `SCAFFOLDED` | Sadece PyMuPDF dijital PDF parser mevcut. OCR, Tesseract, FTS Türkçe yapılandırması eksik. Source locator'lar yetersiz. |
| **Legal Canonical Domain** | `SCAFFOLDED` | Temel Matter modelleri var ancak LegalEntity, LegalAssertion, Claim, EvidenceItem gibi detaylı ilişkisel şemalar eksik. |
| **Legal Extraction Pipeline** | `SCAFFOLDED` | `apps/api/services/legal_extraction.py` gerçek bir pipeline değil. Port/Adapter soyutlaması yok. |
| **Timeline, Claims & Evidence** | `SCAFFOLDED` | API ve UI tarafı büyük oranda statik (mock) veri dönüyor, gerçek bağlantı yok. |
| **Matter Q&A** | `SCAFFOLDED` | `qa.py` var ama RAG akışı (retrieval, citation validation vs.) tam çalışmıyor. |
| **Legal Research** | `SCAFFOLDED` | Source package yönetimi (validate, import, search) yok. Frontend mock Yargıtay dönüyor. |
| **Deadline Engine** | `NOT_STARTED` | `deadline_engine.py` var ama kural motoru (trigger, holiday, review) ve kesin süre hesaplama logic'i eksik. |
| **Draft Studio** | `SCAFFOLDED` | Backend routing TODO. Frontend'de sadece "Tiptap Editor Loaded" metni var. Autosave, citation export eksik. |
| **Notifications & Audit** | `NOT_STARTED` | Merkezi bir audit log ve notification (SSE/email vs.) sistemi yok. |
| **Frontend - Genel Durum** | `SCAFFOLDED` | Next.js yapısı var ama Türkçe/İngilizce karmaşası, `Math.random` hata simülasyonları ve mock veriler ağırlıklı. API base env ile yönetilmiyor. |
| **Idempotency & Concurrency** | `SCAFFOLDED` | `idempotency_keys.key` global unique, tenant/route bazlı değil. ETag/If-Match tabanlı optimistic concurrency uygulanmamış. |
| **Security Hardening** | `NOT_STARTED` | CORS sabit, CSRF, Secure/HttpOnly Cookie, rate limit eksik. |
| **Observability (OTel & Metrics)** | `NOT_STARTED` | JSON loglar ve OTel trace eksik. |
| **Testing** | `SCAFFOLDED` | API'de `assert True` var, frontend CI typecheck vs yapmıyor, Playwright testleri ve gerçek test izolasyonu yok. |
