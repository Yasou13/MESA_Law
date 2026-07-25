## Yapılanlar
- `apps/api/models/parser.py` dosyası ile `ParsedDocument` ve `ParsedPage` modelleri oluşturuldu. FTS (Full Text Search) için `tsvector` kolonu ve GIN indeksi eklendi.
- PyMuPDF kütüphanesi entegre edilerek `apps/worker/parsers/pdf.py` altında `PyMuPDFParser` oluşturuldu. Metin ve bounding box (layout) bilgileri çıkarılabiliyor.
- Veritabanı için gerekli Alembic migration yazılıp uygulandı.
- `apps/worker/test_parser.py` içinde test PDF'si üretilip, PyMuPDF ile ayrıştırılması ve PostgreSQL FTS kullanılarak metin üzerinde tam metin araması (@@ operatörü) başarılı şekilde test edildi.

## Değişen Dosyalar
- `apps/api/models/parser.py` [NEW]
- `apps/api/models/__init__.py`
- `migrations/versions/5122f182a40b_add_parser_models.py` [NEW]
- `apps/worker/parsers/base.py` [NEW]
- `apps/worker/parsers/pdf.py` [NEW]
- `apps/worker/test_parser.py` [NEW]
- `docs/work-orders/WO-007.md` [NEW]
- `docs/handoffs/WO-007-HANDOFF.md` [NEW]
- `pyproject.toml` (PyMuPDF bağımlılığı eklendi)

## Tasarım Kararları
- PyMuPDF'in senkron yapısı nedeniyle parse işlemleri bloklanmayı önlemek adına `run_in_executor` içerisinde iş parçacıklarına (thread) devredildi.
- Bounding box ve benzeri metadata bilgileri `JSON` (veya serialized JSON string) içerisinde layout olarak tutuluyor.
- Arama için Elasticsearch vs yerine öncelikle PostgreSQL FTS tercih edildi (mimari basitliği için).

## Test Sonuçları
```bash
uv run pytest apps/worker/test_parser.py
```
Test başarıyla tamamlandı. `MESA Law` kelimesi PDF içerisinden başarılı şekilde taranıp FTS kullanılarak sorgulandı.

## Sonraki Önerilen Adım
- WO-008 (Intelligence Port ve Mock)
