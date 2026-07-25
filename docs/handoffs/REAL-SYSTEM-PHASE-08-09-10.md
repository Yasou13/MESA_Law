# Phase 8, 9, 10: Legal Core (Parser, Canonical Domain, Extraction) Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- **Faz 8 (Parser, OCR, Source Locator):**
  - `PyMuPDF` (fitz) ve `docx2txt` kütüphaneleri sisteme eklendi.
  - LlamaParse'a ulaşılamadığı durumlarda (`api_key` eksikliği vb.) veya standart PDF analizlerinde fallback mekanizması olarak PyMuPDF ile Bounding-Box (`layout`) veri çıkartımı entegre edildi. DOCX parse yeteneği eklendi.
  - `SourceLocator` ve `BoundingBox` Pydantic şemaları eklendi.
- **Faz 9 (Canonical Legal Domain):**
  - `MatterParty`, `Claim`, `EvidenceItem`, ve `LegalAssertion` gibi gelişmiş hukuki model sınıfları `apps/api/models/domain.py` içerisine eklendi.
  - İlgili Alembic migration'ı oluşturuldu, her bir yeni tabloya `ENABLE ROW LEVEL SECURITY` komutlarıyla Multi-tenant izolasyon (RLS) politikası uygulandı.
- **Faz 10 (Legal Extraction):**
  - AI extraction (çıkarım) işlemleri için Port/Adapter modeli `apps/api/core/extraction.py` içerisinde `LegalExtractionAdapter` arayüzü ile kuruldu.
  - Gerçek AI model entegrasyonu tamamlanana kadar (veya opsiyonel olarak) kullanılacak `MockLegalExtractionAdapter` oluşturuldu.
  - `apps/worker/handlers/extraction.py` yazılarak `EXTRACT_LEGAL_DATA` background job'ı tanımlandı. Bu job, PARSE_DOCUMENT başarılı olduktan sonra tetiklenir ve parse edilen metinleri okuyup Partileri/Talepleri (Parties/Claims) çıkararak `review_status="pending_review"` şeklinde veritabanına Canonical olarak kaydeder.

## Değişen Dosyalar
- `pyproject.toml` (`pymupdf` ve `docx2txt` eklendi)
- `apps/api/schemas/api.py` (SourceLocator)
- `apps/api/models/domain.py` (Yeni domain tabloları eklendi)
- `migrations/versions/df6f1f67d720_add_canonical_domain_models.py` (Oluşturuldu + RLS)
- `apps/worker/handlers/parser.py` (PyMuPDF entegrasyonu + job kuyruklama)
- `apps/api/core/extraction.py` (Yeni Port/Adapter)
- `apps/worker/handlers/extraction.py` (Yeni Worker Handler)
- `apps/worker/main.py` (Extraction job kaydedildi)

## Güvenlik Etkisi
- Sadece `app.current_tenant` değişkenine sahip oturumların ilgili firmaya ait Claim, Evidence, Party ve Assertion kayıtlarına erişebilmesi veritabanı (RLS) düzeyinde güvence altına alındı.

## Sonraki Fazlar
**Faz 11 — Timeline, Claims ve Evidence**
**Faz 12 — Matter Q&A**
**Faz 13 — Legal Research**
Bu fazlarda frontend statik verileri tamamen silinip bu yeni model katmanına bağlanacak.
