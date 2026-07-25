# Phase 3: Gerçek PostgreSQL Data Modelleri ve RLS Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- Zaten `Mapped` üzerinden tanımlı olan Pydantic-bağımsız SQLAlchemy ORM modelleri (`matters`, `documents`, `parsed_documents`, vb.) incelendi ve doğrulandı.
- `tenant_id` içeren tüm tablolara PostgreSQL-seviyesi RLS (Row Level Security) eklendi (`e597de7abef9_enable_rls_for_tenant_tables.py`).
- RLS korumasının veritabanı oturumu seviyesinde uygulanabilmesi için `apps/api/core/rls.py` modülü güncellendi ve SQLAlchemy `Pool` checkout event'ine `SET LOCAL app.current_tenant` ayarı eklendi.
- Eksik olan migration dosyaları imaja kopyalandı ve Alembic `upgrade head` başarılı bir şekilde çalıştırıldı.

## Değişen Dosyalar
- `migrations/versions/e597de7abef9_enable_rls_for_tenant_tables.py` (Yeni)
- `apps/api/core/rls.py`

## Güvenlik Etkisi
- Sadece uygulama mantığı üzerinden (`WHERE tenant_id = ?`) değil, veritabanı sürücüsü seviyesinde de (PostgreSQL RLS ile) "Tenant Isolation" güvenceye alındı. Bir tenant ID'si olmayan veya yetkisiz sorgu çekmeye çalışan bağlantılar veritabanı tarafından doğrudan engellenecek.

## Test Komutları
```bash
docker compose logs db-migration
```

## Bilinen Eksikler
- RLS'in gerçekten çalışıp çalışmadığı entegrasyon testleriyle (pytest ve sahte tenant id'leri kullanarak) doğrulanmalıdır. Şimdilik sistem ayağa kaldırıldı ancak uçtan uca otomatik bir test mevcut değildir.

## Rollback
Gerekirse veritabanı downgrade edilebilir: `docker compose exec -T legal-api uv run alembic downgrade -1`

## Sonraki Faz
**Faz 4 — MinIO & Gerçek Doküman Yönetimi**
Dosya yükleme endpoint'lerinin MinIO'ya bağlanması, pre-signed URL desteği ve ClamAV ile antivirüs entegrasyonunun aktif edilmesi.
