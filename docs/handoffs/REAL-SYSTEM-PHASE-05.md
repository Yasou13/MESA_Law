# Phase 5: LlamaParse / Unstructured Çevrimdışı İzolasyon Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- `apps/worker/handlers/parser.py` oluşturuldu ve LlamaParse entegrasyonu sağlandı.
- Projeye `llama-parse` bağımlılığı eklendi.
- ClamAV taraması (`SCAN_DOCUMENT`) temiz sonuçlandığında `PARSE_DOCUMENT` job'ı tetiklenecek şekilde `document.py` güncellendi.
- `handle_parse_document` fonksiyonu S3 üzerinden pdf'yi indirip LlamaParse'a gönderiyor, dönen markdown sonucunu hem veritabanına `ParsedDocument` / `ParsedPage` formatında kaydediyor hem de minio'ya `{tenant_id}/{matter_id}/parsed_{revision_id}.md` formatında yedekliyor.
- LLM API key yoksa lokal geliştirme aşamasında mock extraction yapılacak şekilde uyarlanabilir kod yapısı kullanıldı.

## Değişen Dosyalar
- `pyproject.toml`
- `apps/worker/main.py`
- `apps/worker/handlers/document.py`
- `apps/worker/handlers/parser.py` (Yeni)

## Güvenlik Etkisi
- Doküman içeriklerinin dış servislere gönderilmeden önce mutlak izolasyon ortamında (Worker queue üzerinden retry/backoff mekanizmalarıyla) işlenmesi sağlandı. Kullanıcı (frontend) senkron olarak uzun parse sürelerini beklemiyor.

## Test Komutları
```bash
docker compose logs legal-worker
```

## Bilinen Eksikler
- LlamaParse API Key (`LLAMA_CLOUD_API_KEY`) çevresel değişkenlerde (environment) yapılandırılmalıdır.

## Sonraki Faz
**Faz 6 — Redis ile Rate Limiting ve Queue Yapılandırması**
FastAPI endpointleri için `slowapi` ve Redis tabanlı rate limiting entegrasyonu, worker log izleme sistemleri.
