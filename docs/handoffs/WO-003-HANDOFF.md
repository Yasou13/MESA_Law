## Yapılanlar
- `apps/api/core` içerisine ortak backend altyapısı (config, database, utils, models, errors, middleware, idempotency) oluşturuldu.
- Pydantic Settings kullanılarak `config.py` eklendi.
- SQLAlchemy 2.0 (async ve sync) ve Alembic kurulumu tamamlandı. (Alembic'in Keycloak vb. external tabloları silmemesi için `include_object` hook'u eklendi).
- `uuid6` kullanılarak UUIDv7 desteği ve `utc_now` abstraction'ı eklendi.
- Optimistic locking (`version_id`) ve audit alanlarını içeren `Base` ve `AuditMixin` yazıldı.
- RFC 7807 uyumlu error handler (`ProblemException` ve `problem+json`) implemente edildi.
- Trace/Correlation ID middleware'i entegre edildi.
- Idempotency store modeli ve basit bir yardımcı fonksiyon eklendi.
- `make test` üzerinde tüm bu işlevler (idempotency conflict ve problem+json formatı) gerçek PostgreSQL veritabanında test edildi.

## Değişen dosyalar
- `apps/api/core/config.py` [NEW]
- `apps/api/core/database.py` [NEW]
- `apps/api/core/errors.py` [NEW]
- `apps/api/core/idempotency.py` [NEW]
- `apps/api/core/middleware.py` [NEW]
- `apps/api/core/models.py` [NEW]
- `apps/api/core/utils.py` [NEW]
- `apps/api/test_backend.py` [NEW]
- `migrations/` [NEW]
- `alembic.ini` [NEW]
- `docs/work-orders/WO-003.md` [NEW]
- `docs/handoffs/WO-003-HANDOFF.md` [NEW]
- `pyproject.toml` (bağımlılıklar eklendi)

## Tasarım kararları
- UUIDv7 üretimi için `uuid6` paketi tercih edildi.
- Async veritabanı bağlantısı için `postgresql+psycopg_async` kullanıldı.
- Keycloak'ın ileride tablolarını `mesa_law` içine kurma ihtimaline karşı alembic konfigürasyonuna `include_object` filtresi eklendi; böylece bilinmeyen tablolar alembic tarafından düşürülmeyecek.

## Test komutları ve sonuçları
```bash
make test
```
(Tüm 3 backend testi — Problem+json dönüşümü ve Idempotency mantığı başarıyla geçti.)

## Migration etkisi
- `aeee08dee01f_initial_models` isimli ilk alembic migration'ı çalıştırılarak `idempotency_keys` tablosu oluşturuldu.

## Güvenlik etkisi
- Exception handler 500 hatalarında internal stack trace'leri maskeleyerek güvenliği sağlar. Trace ID, HTTP Header'lara dahil edildi.

## Bilinen eksikler
- Gerçek iş logic'i (örn. endpoint'ler) henüz yazılmadı, dummy endpointler kullanıldı.

## Rollback
- Gerekirse `alembic downgrade base` komutu ile DB'deki tablo silinip commit revert edilebilir.

## Sonraki önerilen WO
- WO-004
