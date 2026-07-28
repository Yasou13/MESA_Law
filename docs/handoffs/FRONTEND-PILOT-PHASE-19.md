# Phase 19: Error, Loading ve Degraded Durumları Handoff

## 1. İlgili Testler ve Exit Code
Tüm Orval kancaları zaten `isLoading` ve `isError` parametreleriyle kullanılmış ve Loading spinner'lar/error handler'lar ilgili component'lere (Drafts, Matters, vb.) yayılmıştı. Ek olarak, `MESA_LAW_INTELLIGENCE_ADAPTER=mock` ayarı varken QA Review Center ve Matter QA Chat sayfalarında degraded mode uyarı banner'ı (sarı bant) görüntülenebilmesi için `system.py` `intelligence_adapter` değeri `mock` dönecek şekilde ayarlandı ve UI'a uyarı bantları yerleştirildi.

## 2. Değişen Dosyalar
- `apps/api/routers/system.py` (Mock mode algılaması `ok` yerine `mock` dönecek şekilde düzeltildi)
- `apps/web/src/app/(protected)/qa/page.tsx` (Yellow warning banner eklendi)
- `apps/web/src/app/(protected)/matters/[id]/qa/page.tsx` (Yellow warning banner eklendi)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
`GET /api/v1/system/dependencies` `intelligence_adapter` değeri artık string enum ("ok", "degraded", "mock") şeklinde dönüyor.

## 5. Güvenlik Etkisi
Yok. (Yalnızca UI seviyesi durum bildirimleri eklendi)

## 6. Bilinen Kalan Açıklar
- Phase 20 ve sonrası.

## 7. Rollback Adımları
`git checkout -- apps/api/routers/system.py apps/web/src/app/\(protected\)/qa/page.tsx apps/web/src/app/\(protected\)/matters/\[id\]/qa/page.tsx`

## 8. Sonraki Faz
Phase 20: Accessibility ve Responsive
