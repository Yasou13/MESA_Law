# Phase 13: Draft Studio Handoff

## 1. İlgili Testler ve Exit Code
FastAPI `draft-studio` router'ına yeni global `GET /drafts` ucu eklendi. Frontend UI'da liste ekranı (`/drafts`) ve editör ekranı (`/drafts/[id]`) derlendi.

## 2. Değişen Dosyalar
- `apps/api/routers/draft_studio.py` (Yeni: `GET /drafts` endpointi eklendi)
- `apps/web/src/app/(protected)/drafts/page.tsx` (Draft listesi sayfası eklendi)
- `apps/web/src/app/(protected)/drafts/[id]/page.tsx` (Sade bir textarea içeren, kaydetme özellikli Draft editörü oluşturuldu)
- `apps/web/src/app/(protected)/matters/[id]/page.tsx` (Matter detaya "Create Draft" butonu eklendi, hook üzerinden POST atılarak yeni taslak oluşturulup editöre yönlendirme (push) bağlandı)
- `apps/web/src/components/Sidebar.tsx` (Drafts navigasyon linki eklendi)

## 3. Eklenen Migration
Yok. Tablolar halihazırda audit geçmişi ile (version control) beraber Alembic üzerinden deploy edilmişti.

## 4. API Sözleşmesi Etkisi
`GET /drafts` tenant seviyesinde eklenmiş oldu.

## 5. Güvenlik Etkisi
Her okuma, değiştirme (PUT) ve listeleme işlemi `tenant_id` kontrolünden geçmektedir. IDOR güvenlik açıkları RLS ile engellenmiştir.

## 6. Bilinen Kalan Açıklar
- Phase 14 (External-Use Approval) henüz yapılmadı.

## 7. Rollback Adımları
`git checkout -- apps/api/routers/draft_studio.py apps/web/src/components/Sidebar.tsx apps/web/src/app/\(protected\)/matters/\[id\]/page.tsx`
`rm -rf apps/web/src/app/\(protected\)/drafts`

## 8. Sonraki Faz
Phase 14: External-Use Approval
