## Yapılanlar
- `Firm`, `User`, `Membership` ve `Matter` (TenantAwareMixin miraslı) modelleri oluşturuldu (`apps/api/models/domain.py`).
- RLS Bypass Guard mekanizması kuruldu: `TenantAwareMixin` türündeki sınıflara sorgu yapılırken aktif bir tenant bağlamı (context) yoksa SQLAlchemy `do_orm_execute` event listener ile intercept edilip `RuntimeError` fırlatılması sağlandı. Bu sayede developer'lar tenant filtresini atlayan kod yazamayacak.
- `apps/api/core/security.py` içerisinde Keycloak auth dev mock yapısı ve `fastapi-csrf-protect` tabanlı CSRF mekanizması eklendi.
- `apps/api/test_auth_rls.py` test dosyası eklenerek RLS guard'ın koruma sağladığı (bypass edilemediği) ve tenant'lar arası izolasyonun çalıştığı doğrulandı.

## Değişen Dosyalar
- `apps/api/core/models.py` (TenantAwareMixin eklendi)
- `apps/api/core/rls.py` [NEW]
- `apps/api/core/security.py` [NEW]
- `apps/api/models/__init__.py` [NEW]
- `apps/api/models/domain.py` [NEW]
- `apps/api/test_auth_rls.py` [NEW]
- `migrations/env.py` (Modeller alembic için import edildi)
- `docs/work-orders/WO-004.md` [NEW]
- `docs/handoffs/WO-004-HANDOFF.md` [NEW]
- `pyproject.toml` (Yeni bağımlılıklar: python-jose[cryptography], fastapi-csrf-protect vb.)

## Tasarım Kararları
- RLS korumasında PostgreSQL yerleşik RLS mekanizması (SET LOCAL role/tenant vs) kullanmak yerine, SQLAlchemy seviyesinde `with_loader_criteria` yöntemi tercih edilerek connection pooling (psycopg_async) sorunlarının önüne geçildi. Bu yapı, bindparam kullanarak dinamik execution-time validasyonu sağlar.
- CSRF validasyonu için FastAPI bağımlılık sistemi `Depends(verify_csrf)` kullanılabilir hale getirildi.

## Test Sonuçları
Tüm 5 test (`test_api.py`, `test_backend.py`, `test_auth_rls.py`) PostgreSQL üzerinde hatasız geçmiştir.
```bash
make test
```

## Sonraki Önerilen Adım
- WO-005 (Worker Queue, Celery/Arq ve OTel Instrumentations)
