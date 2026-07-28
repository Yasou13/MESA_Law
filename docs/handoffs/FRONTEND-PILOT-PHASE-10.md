# Phase 10: Deadlines Frontend Handoff

## 1. İlgili Testler ve Exit Code
FastAPI tarafına deadlines router eklendi ve openapi/orval ile client hookları üretildi. UI sayfası derlendi.

## 2. Değişen Dosyalar
- `apps/api/routers/deadlines.py` (Yeni: `GET /api/v1/deadlines` ve `POST /api/v1/deadlines/{id}/complete`)
- `apps/api/main.py` (Router mount edildi)
- `apps/web/src/app/(protected)/deadlines/page.tsx` (Deadlines listesi, gecikme (overdue) durumu ve "Mark Complete" butonu eklendi)
- `apps/web/src/components/Sidebar.tsx` (Deadlines linki navigasyona eklendi)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
`deadlines` uçları (list ve complete) oluşturuldu, status=`PENDING` yerine `is_completed=False` şeklinde filter edilerek çalıştırıldı. 

## 5. Güvenlik Etkisi
Her okuma/yazma işlemi `tenant_id` kullanılarak kontrol edilir.

## 6. Bilinen Kalan Açıklar
- Phase 11 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`rm apps/api/routers/deadlines.py apps/web/src/app/\(protected\)/deadlines/page.tsx`
`git checkout -- apps/api/main.py apps/web/src/components/Sidebar.tsx`

## 8. Sonraki Faz
Phase 11: Global ve Matter Q&A
