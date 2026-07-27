# Phase 2 Handoff: Keycloak, NextAuth, Caddy ve Docker networking

## İlgili testleri çalıştır & Ham komut çıktısı
- `docker compose --profile core config` başarılı şekilde çalıştı ve yaml çıktısı onaylandı.
- MESA_LAW_KEYCLOAK_ISSUER ve NEXTAUTH değişkenlerinin değerleri doğru şekilde config içine dahil edildi.

## Değişen dosyalar
- `docker-compose.yml`: API ve Web servisleri için Public ve Internal Keycloak network ayarları (ISSUER vs URL ayrımı) yapıldı.
- `docker/Caddyfile`: `/api/auth/*` trafiği `web:3000` portuna, diğer `/api/v1/*` trafiği `legal-api:8001` portuna yönlendirilecek şekilde düzeltildi.
- `apps/web/.env.local`: `NEXT_PUBLIC_MESA_LAW_API_BASE_URL=/api/v1` olarak ayarlanıp hardcoded hostname kaldırıldı.

## Eklenen migration'lar
Yok.

## Güvenlik etkisi
- Public/Internal Issuer ayrımı yapılarak, backend'in browser üzerinden gelen Public Issuer token'ları doğrulayabilmesi ancak Keycloak ile iletişim kurarken iç Docker network'ünü (`http://keycloak:8080`) kullanabilmesi sağlandı (Server-side forging engellendi).
- Caddy reverse proxy API route karmaşası giderildi, yetkisiz `/api/auth` backend erişimleri engellendi.

## Rollback adımları
```bash
git checkout docker-compose.yml docker/Caddyfile apps/web/.env.local
docker compose down && docker compose --profile core up -d
```
