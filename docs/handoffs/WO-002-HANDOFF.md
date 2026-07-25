## Yapılanlar
- `docker-compose.yml` MESA-Law root dizinine oluşturuldu.
- `core` profili tanımlanarak şu temel servisler eklendi: PostgreSQL, MinIO, Redis, Keycloak, ClamAV, Caddy, OTel/Grafana stack, web, legal-api, legal-worker.
- `make dev-doctor` hedefine Docker statüsünü kontrol eden komut (`docker compose --profile core ps`) dahil edildi.
- Servisler başarıyla ayağa kaldırıldı, hacim (volume) kalıcılık testi yapıldı.

## Değişen dosyalar
- `docker-compose.yml` [NEW]
- `docs/work-orders/WO-002.md` [NEW]
- `docs/handoffs/WO-002-HANDOFF.md` [NEW]
- `Makefile` [MODIFY]

## Tasarım kararları
- MESA-Law `docker-compose.yml` içerisindeki şifre yönetimi `${ENV_VAR:-default_value}` şeklinde tasarlanarak `.env` ve varsayılan geliştirme parolası uyumlu hale getirildi.
- MESA servisi plana uygun olarak core profilinden (ve tamamen docker-compose.yml'den) şimdilik hariç tutuldu.

## Test komutları ve sonuçları
```bash
docker compose --profile core up -d
docker compose --profile core down
docker compose --profile core up -d
make dev-doctor
```
(Tüm servislerin başarıyla ve veri kaybı olmadan ayağa kalktığı teyit edildi)

## Migration etkisi
- Yok. Veritabanı tabloları henüz oluşturulmadı.

## Güvenlik etkisi
- Varsayılan şifreler üretim ortamında kesinlikle override edilmelidir.

## Bilinen eksikler
- Keycloak initial realm/client verileri içeri aktarılmadı.
- Grafana/Tempo yapılandırmaları temel ayarları kullanıyor, spesifik dashboard configleri henüz yok.

## Rollback
- `docker compose down -v` komutu çalıştırılıp, commit revert edilebilir.

## Sonraki önerilen WO
- WO-003
