# Phase 14: External-Use Approval Handoff

## 1. İlgili Testler ve Exit Code
FastAPI draft-studio router'ında `approve` ucu test edildi. Frontend UI üzerinden "Approve" butonuna basıldığında durum "APPROVED_FOR_EXTERNAL_USE" olarak başarıyla kaydedildi.

## 2. Değişen Dosyalar
- `apps/api/routers/draft_studio.py` (Yeni: `POST /api/v1/draft-studio/drafts/{draft_id}/approve` endpoint'i eklendi. Tüm okuma endpoint'lerinde `status` alanı modele dahil edildi.)
- `apps/web/src/app/(protected)/drafts/[id]/page.tsx` (Draft editörünün header kısmına "Approve" butonu eklendi, draft zaten onaylanmışsa "Approved" statik etiketi gösteriliyor.)

## 3. Eklenen Migration
Yok. `Draft` tablosunda halihazırda `status` kolonu mevcuttu.

## 4. API Sözleşmesi Etkisi
`POST /draft-studio/drafts/{id}/approve` eklendi, Draft objesinin status alanı UI tarafından tüketilmeye başlandı.

## 5. Güvenlik Etkisi
`approve` endpoint'i `tenant_id` doğrulaması içermektedir.

## 6. Bilinen Kalan Açıklar
- Phase 15 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`git checkout -- apps/api/routers/draft_studio.py apps/web/src/app/\(protected\)/drafts/\[id\]/page.tsx`

## 8. Sonraki Faz
Phase 15: Notifications ve Operations
