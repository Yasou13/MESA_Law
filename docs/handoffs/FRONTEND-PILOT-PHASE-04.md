# Phase 4: Gerçek Dashboard Handoff

## 1. İlgili Testler ve Exit Code
`dashboard.py` eklenip FastAPI openapi speğine entegre edildi. `pnpm run api:generate` ile Orval tarafından API hooku başarıyla üretildi.

## 2. Değişen Dosyalar
- `apps/api/routers/dashboard.py` (Yeni: `GET /api/v1/dashboard/metrics`)
- `apps/api/main.py` (Dashboard router'ı eklendi)
- `apps/web/src/api/endpoints/dashboard/` (Orval tarafından oluşturulan API client hookları)
- `apps/web/src/app/(protected)/dashboard/page.tsx` (Statik veriler kaldırılarak gerçek API hookuna, loading, error ve retry state'lerine geçildi. Deep link eklendi.)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
`GET /api/v1/dashboard/metrics` ucu eklendi. Aktif matter'ları, pending review'leri, deadline'ları, unread notification'ları ve degraded capability'leri döner.

## 5. Güvenlik Etkisi
Tenant Isolation, `setup_tenant_context` dependency ile sağlandı ve metrikler tamamen ilgili `tenant_id` context'i filtrelenerek getiriliyor.

## 6. Bilinen Kalan Açıklar
- Phase 5 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`git checkout -- apps/api/main.py apps/web/src/app/\(protected\)/dashboard/page.tsx`
`rm apps/api/routers/dashboard.py`

## 8. Sonraki Faz
Phase 5: Eksik Global Route'lar
