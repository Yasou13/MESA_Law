# Phase 7: Web Arayüzü: Next.js + TailwindCSS + Shadcn/UI ile Core Kurulum Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- `apps/web/package.json` güncellenerek `lucide-react`, `clsx`, `tailwind-merge` ve `react-hot-toast` frontend bağımlılıkları PNPM workspace ile kuruldu.
- Zaten var olan `@tanstack/react-query` paketi kullanılarak veri çekme/manipülasyonu sağlandı.
- `apps/web/src/app/providers.tsx` içerisine `QueryClientProvider` eklendi, global sarmalayıcı aktif edildi.
- `apps/web/src/app/layout.tsx` içerisine `<Toaster />` eklenerek Shadcn tarzı kullanıcı dostu bildirim altyapısı hazırlandı.
- `apps/web/src/app/matters/page.tsx` sayfası güncellendi. Kullanıcıların (tenant izole) matter'larını görebildiği ve anında yeni matter oluşturabildiği React Query temelli asenkron (loading/spin states içeren) bir arayüz kodlandı.
- `apps/web/src/app/matters/[id]/page.tsx` detay sayfası oluşturuldu. 
  - Backend API (`POST /upload-intent`) aracılığıyla MinIO / S3 Pre-signed URL'i çekildi.
  - S3 URL'sine doğrudan `axios.put` ile dosya yükleme, Shadcn-vari animasyonlu yükleme barı (progress bar) desteğiyle arayüze eklendi.
  - İşlem sonunda `complete` endpointi çağrılarak backend worker'larına (SCAN -> PARSE) sinyal gönderimi sağlandı.

## Değişen Dosyalar
- `pnpm-lock.yaml`
- `apps/web/package.json`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/providers.tsx`
- `apps/web/src/app/matters/page.tsx`
- `apps/web/src/app/matters/[id]/page.tsx` (Yeni)

## Güvenlik Etkisi
- S3 upload işlemlerinin güvenliği (Sunucu yormadan doğrudan MinIO'ya) ve presigned url timeout limitleriyle kısıtlanması UI tarafında tam desteklenir hale geldi.

## Sonraki Faz
**Faz 8 — Frontend-Backend Uçtan Uca (E2E) Test Hazırlığı**
Tüm bu ilk 7 fazın manuel testle kalmayıp, CI/CD süreçlerinde Playwright veya pytest tabanlı uçtan uca otomatik testlerle garanti altına alınması.
