# Phase 15: Notifications ve Operations Handoff

## 1. İlgili Testler ve Exit Code
Sidebar bileşeni için Notification API entegre edildi ve okunmamış bildirim (unread) kırmızı nokta UI'ı eklendi. OperationsMenu bileşeni için System API (`/api/v1/system/dependencies`) çağrıldı ve Worker durumları Health status'e bağlandı.

## 2. Değişen Dosyalar
- `apps/web/src/components/Sidebar.tsx` (`useGetNotificationsApiV1NotificationsGet` ile okunmamış bildirim sayısı çekildi ve render edildi)
- `apps/web/src/components/OperationsMenu.tsx` (`useSystemDependenciesApiV1SystemDependenciesGet` ile dependency sağlık durumları çekilip arayüze (Healthy / Issues Detected) aktarıldı)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
Zaten var olan `system` ve `notifications` router'ları kullanıldı.

## 5. Güvenlik Etkisi
Her iki uç da ya tenant auth gerektiren veya admin auth gerektiren (system) endpoint'lerdir. UI'da React Query ile güvenli şekilde render edildiler.

## 6. Bilinen Kalan Açıklar
- Phase 16 (Admin Panel) ve sonrası.

## 7. Rollback Adımları
`git checkout -- apps/web/src/components/Sidebar.tsx apps/web/src/components/OperationsMenu.tsx`

## 8. Sonraki Faz
Phase 16: Admin Panel
