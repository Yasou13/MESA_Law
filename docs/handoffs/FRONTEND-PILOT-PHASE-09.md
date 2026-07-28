# Phase 9: OCR Hata Akışı Handoff

## 1. İlgili Testler ve Exit Code
`matters/[id]/page.tsx` ve `documents/[id]/page.tsx` dosyaları statik olarak derlendi. Backend'den gelecek 400 ve 422 hataları `toast` aracılığıyla gösterilmek üzere entegre edildi. Karantina ekranı uyarısı başarıyla eklendi.

## 2. Değişen Dosyalar
- `apps/web/src/app/(protected)/matters/[id]/page.tsx` (Upload işlemindeki catch bloğu, `err.response?.data?.detail` okuyacak şekilde güncellendi, böylece ZIP bomb, active content vb. hatalar UI'da görünür oldu)
- `apps/web/src/app/(protected)/documents/[id]/page.tsx` (`quarantined` veya `infected` statülerinde ekrana kocaman kırmızı bir "SECURITY ALERT" banner'ı eklendi ve preview/download tamamen engellendi)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
Mevcut UploadIntent ve completeUpload uçlarından dönen HTTP 400 hata mesajları artık frontend tarafından tüketiliyor.

## 5. Güvenlik Etkisi
Kullanıcının virüslü veya tehlikeli (JS içeren PDF) belgelere kazara erişimi engellendi; hem backend (presigned url vermez) hem de frontend (UI gizler) katmanlı bir savunma sergiliyor.

## 6. Bilinen Kalan Açıklar
- Phase 10 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`git checkout -- apps/web/src/app/\(protected\)/matters/\[id\]/page.tsx apps/web/src/app/\(protected\)/documents/\[id\]/page.tsx`

## 8. Sonraki Faz
Phase 10: Deadlines Frontend
