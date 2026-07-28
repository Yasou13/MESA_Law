# Phase 23: MESA V4 Gerçek Sync Handoff

## 1. İlgili Testler ve Exit Code
Matter detay sayfasına (frontend) "Sync with MESA Core" butonu yerleştirildi. Bu buton `POST /api/v1/matters/{id}/rebuild-mesa` endpoint'ini tetikleyerek `MesaSyncService` üzerinden backend ile iletişim kurar ve ilgili Matter'daki tüm dokümanların ayrıştırılmış (parsed) sayfalarını Ingestion port'u üzerinden MESA Core'a gönderir. Frontend'de başarılı bir şekilde toast mesajı ile entegre edilmiştir.

## 2. Değişen Dosyalar
- `apps/web/src/app/(protected)/matters/[id]/page.tsx` (Rebuild MESA butonu eklendi, `useRebuildMatterMesa` çağrıldı)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
Zaten `apps/api/routers/matters.py`'da olan `POST /matters/{matter_id}/rebuild-mesa` orval ile bağlandı.

## 5. Güvenlik Etkisi
`rebuild-mesa` endpoint'i `setup_tenant_context` bağımlılığını kullanarak, o anki kullanıcının yalnızca yetkili olduğu firmanın Matter verilerini çekmesini (RLS) sağlar. Sızma veya tenant kaçağı yoktur.

## 6. Bilinen Kalan Açıklar
- Phase 24 (CI / Son Testler)

## 7. Rollback Adımları
`git checkout -- apps/web/src/app/\(protected\)/matters/\[id\]/page.tsx`

## 8. Sonraki Faz
Phase 24: CI ve Temiz Stack Kabul Testi
