# MESA Law - Real System Baseline Audit

**Tarih**: 2026-07-28
**Durum**: BLOCKED (Kontrollü Pilot Adayı Değil)

## Genel Değerlendirme
MESA Law projesi üzerinde yapılan Faz 0 denetimlerinde, kod tabanında birçok modülün yer aldığı ancak sistemin genelinde ciddi runtime, auth ve entegrasyon problemleri olduğu tespit edilmiştir. 
Mock veriler, simüle edilmiş ekranlar, yetersiz testler ve kırık database constraintleri sistemin bir pilot aşamasına geçişini engellemektedir.

## Modül Durumları

| Modül | Durum | Açıklama |
|---|---|---|
| Authentication & Tenant | IMPLEMENTED (Hatalı) | `auth.py` içinde tanımsız `tenant_id` kullanımı mevcut. Frontend hâlâ `x-tenant-id` gönderiyor. Cross-tenant izolasyonu tam kanıtlanmamış. |
| Database & Roles | IMPLEMENTED (Hatalı) | Migration öncesinde runtime hesapları ayağa kalkıyor. Uygulama superuser yetkileriyle RLS atlıyor olabilir. Postgres üzerinde RLS testleri FAILED. |
| Extraction & ReviewItem | IMPLEMENTED (Hatalı) | `status='draft'` gibi enum dışı değerler ve `unknown` gibi yabancı anahtarlar kullanılıyor. OCR_FAILED teknik mesajı içerik olarak indexleniyor. |
| Canonical Publication | IMPLEMENTED (Hatalı) | Birden fazla publisher (SYNC_APPROVED_REVIEWS vb.) mevcut. `corrected_content` her zaman kullanılmıyor. Bağımlılık (Claim-Party) kontrolleri zayıf. |
| Deadlines | SCAFFOLDED | Hardcoded ekranlar, trigger tarihi olmayan veriler, enum dışı durumlar (`under_review`). |
| Q&A ve Citations | SCAFFOLDED | Global Q&A `setTimeout` ile simüle edilmiş. Belge sohbeti mock yanıtlar dönüyor. Kaynak yönetişimi eksik. |
| Frontend Entegrasyonu | IMPLEMENTED (Hatalı) | UI stublar, `Math.random` destek erişim kodları, zayıf permission guardlar. Test ve derleme hataları mevcut (18 lint hatası, typescript hataları). |
| CI / CD / Testler | FAILED | 41 adet pytest hatası. `pnpm typecheck` ve `lint` geçmiyor. `.python-version` belirsiz. Mock E2E tokenler hâlâ kullanımda. |

## Sonuç
Pilot geçişi öncesinde, yukarıdaki eksikliklerin MESA Core projesine dokunmadan, gerçek PostgreSQL/Keycloak/MinIO bağımlılıklarıyla çözülmesi ve testlerin tam olarak PASS durumuna getirilmesi gerekmektedir.
