## Yapılanlar
- S3/MinIO uyumlu Object Storage servisi (`apps/api/core/storage.py`) oluşturuldu. `aioboto3` kütüphanesi entegre edildi.
- İstemcilerin (Frontend) doğrudan MinIO'ya güvenli yükleme/indirme yapabilmesi için `generate_presigned_upload_url` ve `generate_presigned_download_url` metodları yazıldı.
- `apps/api/models/document.py` içerisinde `Document` ve `DocumentRevision` modelleri oluşturuldu.
- `DocumentRevision` tablosunda `s3_key` eşsiz (unique) yapılarak overwrite engellendi (immutable key tasarımı).
- Yüklenen dosyaların Chain of Custody (hash) ve Karantina (`scan_status`: uploading, clean, infected vb.) aşamalarını takip edecek kolonlar modele eklendi.
- Yeni modeller Alembic kullanılarak veritabanına geçirildi (migration eklendi).
- Model izolasyonu ve Presigned URL üretimi `apps/api/test_storage.py` ile test edilerek doğrulandı.

## Değişen Dosyalar
- `apps/api/core/storage.py` [NEW]
- `apps/api/models/document.py` [NEW]
- `apps/api/models/__init__.py`
- `apps/api/test_storage.py` [NEW]
- `migrations/versions/05f0047c3d60_add_document_models.py` [NEW]
- `docs/work-orders/WO-006.md` [NEW]
- `docs/handoffs/WO-006-HANDOFF.md` [NEW]
- `pyproject.toml` (`aioboto3` bağımlılığı eklendi)

## Tasarım Kararları
- S3 entegrasyonu tamamen asenkron (async/await) yapıldı.
- Veri modellemesinde; fiziksel dosyaların (s3_key) asla güncellenmeyeceği, bunun yerine yeni bir `DocumentRevision` olarak ekleneceği (append-only) "canonical" yapı kullanıldı.

## Test Sonuçları
```bash
uv run pytest apps/api/test_storage.py
```
Testler MinIO entegrasyonuyla (gerçek bucket head/create) ve PostgreSQL üzerinde başarılı oldu.

## Sonraki Önerilen Adım
- WO-007 (Parser/OCR Canonical Artifacts)
