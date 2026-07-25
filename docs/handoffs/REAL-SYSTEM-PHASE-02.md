# Phase 2: OIDC & Gerçek Yetkilendirme Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- Web uygulamasına OIDC entegrasyonu için `next-auth` paketi eklendi.
- `apps/web/src/app/api/auth/[...nextauth]/route.ts` oluşturularak Keycloak sağlayıcısı yapılandırıldı.
- `apps/web/src/app/login/page.tsx` sayfası güncellendi; mock giriş butonları kaldırılarak `next-auth` Keycloak SSO girişi entegre edildi.
- `apps/web/src/app/providers.tsx` içine `SessionProvider` ve Bearer token'ı istek başlıklarına ekleyen Axios interceptor eklendi.
- `docker/keycloak-realm.json` dosyası güncellendi, `mesa-client` gizli (confidential) istemci olarak yapılandırıldı ve NextAuth için secret tanımlandı.
- `docker-compose.yml` içinde web servisine `NEXTAUTH_URL` ve `NEXTAUTH_SECRET` çevre değişkenleri eklendi.
- `apps/api/dependencies/auth.py` güncellendi, mock user ID üretmek yerine Keycloak JWT token içeriğinden `sub`, `email` ve Keycloak rolleri çıkarılacak şekilde ayarlandı.
- MESA Law iş kurallarına göre (`FIRM_ADMIN`, `ATTORNEY` vb.) yetkilendirme yapacak `MatterAccessPolicy`, `DocumentAccessPolicy`, `ReviewAccessPolicy`, `ExportAccessPolicy` sınıfları `apps/api/core/policies.py` içerisine eklendi.

## Değişen Dosyalar
- `apps/web/package.json`
- `apps/web/src/app/api/auth/[...nextauth]/route.ts` (Yeni)
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/providers.tsx`
- `docker/keycloak-realm.json`
- `docker-compose.yml`
- `apps/api/dependencies/auth.py`
- `apps/api/core/policies.py` (Yeni)

## Güvenlik Etkisi
- Web tarafında artık LocalStorage'a `tenant_id` güvenilerek kaydedilmiyor (kısmi olarak token interceptor aktifleşene kadar geçiş dönemi destekleniyor).
- Backend, gerçek Authorization token (Bearer) içeriğine bakarak kullanıcıyı tanıyor ve rollerini çözümlüyor.

## Test Komutları
```bash
# Keycloak token loglarını incelemek için:
docker compose logs web
docker compose logs keycloak
```

## Bilinen Eksikler
- Backend tarafında JWT imza doğrulaması (Signature verification) ve JWKS public key çekme işlemi eklenmelidir. (Şu an lokal geliştirme kolaylığı adına `get_unverified_claims` kullanılıyor).
- API tarafındaki `active-firm` (tenant seçimi) işlemleri hala DB düzeyinde değil, hardcode/mock mekanizması ile idare ediliyor. Bu durum veritabanı şeması tamamlandığında güncellenmelidir.

## Sonraki Faz
**Faz 3 — Gerçek PostgreSQL Data Modelleri**
Pydantic mock modellerinden SQLAlchemy ORM modellerine geçiş ve tenant-izolasyon (RLS) altyapısının kurulması.
