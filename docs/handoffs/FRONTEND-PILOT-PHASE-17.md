# Phase 17: Firma Değiştirme Akışı Handoff

## 1. İlgili Testler ve Exit Code
`apps/web/src/lib/api/client.ts` üzerinde axios interceptor'ı düzenlendi. `localStorage.getItem('mesa_tenant_id')` değeri okunarak `x-tenant-id` header'ı olarak eklendi.
`Sidebar.tsx` içine Firma değiştirme dropdown menüsü eklendi. `useListUserFirms` ve `useSetActiveFirmApiV1SessionActiveFirmPost` uçları başarıyla bağlandı.

## 2. Değişen Dosyalar
- `apps/web/src/lib/api/client.ts` (tenant-id header'ı axios requestlerine eklendi)
- `apps/web/src/components/Sidebar.tsx` (Firma dropdown menüsü ve `switch-firm` logic'i uygulandı)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
Yok. Zaten var olan `session` ve `firms` uçları kullanıldı.

## 5. Güvenlik Etkisi
`session/active-firm` ucu, kullanıcının talep ettiği firmada aktif bir üye olup olmadığını kontrol edip auth yapmaktadır. RLS kuralları backend tarafında korunmaktadır.

## 6. Bilinen Kalan Açıklar
- Phase 18 (Design System) ve sonrası.

## 7. Rollback Adımları
`git checkout -- apps/web/src/components/Sidebar.tsx apps/web/src/lib/api/client.ts`

## 8. Sonraki Faz
Phase 18: Design System ve Durum Yönetimi
