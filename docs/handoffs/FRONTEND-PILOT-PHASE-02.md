# Phase 2: API Client ve URL Mimarisi Handoff

## 1. İlgili Testler ve Exit Code
- `pnpm run api:generate` başarıyla çalıştı ve `orval.config.js` ayarları kullanılarak yeni API client `src/api/endpoints` altına generate edildi.

## 2. Değişen Dosyalar
- `apps/web/package.json` (`api:generate` komutu `orval.config.js` kullanacak şekilde düzeltildi)
- `apps/web/orval.config.js` (Mutator path güncellendi)
- `apps/web/src/lib/api/client.ts` (Yeni merkezi API client; hata yönetimi eklendi)
- `apps/web/.env.local` (Double prefix sorununu çözmek için `NEXT_PUBLIC_MESA_LAW_API_BASE_URL` origin root yapıldı)
- `apps/web/src/lib/axios.ts` (Silindi, yerine `client.ts` geldi)

## 3. Eklenen Migration
None.

## 4. API Sözleşmesi Etkisi
Orval tarafından üretilen tüm servis çağrıları (Axios requestleri) artık yeni merkezi `client.ts` üzerinden geçecek. Her isteğe session token eklenecek ve Problem+JSON formatındaki backend dönüşleri kullanıcı dostu mesajlara (toast) dönüştürülecek.

## 5. Güvenlik Etkisi
Session tokenları NextAuth getSession() üzerinden alınıyor. Hatalar merkezi ele alınarak token expire (401) olduğunda güvenli `signOut` yönlendirmesi yapılıyor.

## 6. Bilinen Kalan Açıklar
- Phase 3 ve sonrası maddeler henüz uygulanmadı.

## 7. Rollback Adımları
`git checkout -- apps/web/package.json apps/web/orval.config.js apps/web/.env.local`

## 8. Sonraki Faz
Phase 3: Gerçek Keycloak ve Session Akışı.
