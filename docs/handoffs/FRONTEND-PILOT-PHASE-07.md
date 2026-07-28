# Phase 7: ReviewItem -> Canonical Backend Akışı Handoff

## 1. İlgili Testler ve Exit Code
Manuel kod analizi ve statik analiz gerçekleştirildi. Kod başarıyla fastapi tarafında entegre edildi.

## 2. Değişen Dosyalar
- `apps/api/routers/reviews.py` (Approve endpoint'ine ReviewItem entity_type'a göre MatterParty, Claim veya DeadlineCandidate yaratıp DB'ye yazan "Canonical Data Ownership" blokları eklendi.)

## 3. Eklenen Migration
Yok. Tablolar zaten Alembic üzerinden deploy edilmiş halde (baseline audit sırasında teyit edilmişti).

## 4. API Sözleşmesi Etkisi
`POST /api/v1/reviews/{id}/approve` çağrısı, veriyi sadece `approved` state'e çekmekle kalmaz, asıl domain objesini de oluşturur.

## 5. Güvenlik Etkisi
Review id, her halükarda kullanıcının dahil olduğu tenant_id'ye göre kontrol edildikten sonra (Tenant-Level İzolasyon) canonical tablolara yine aynı tenant_id ile kaydedilir. İzinsiz erişim sıfıra indirgenir.

## 6. Bilinen Kalan Açıklar
- Phase 8 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`git checkout -- apps/api/routers/reviews.py`

## 8. Sonraki Faz
Phase 8: Belge Merkezi ve Viewer
