# Phase 4: MinIO & Gerçek Doküman Yönetimi Teslimat Raporu

## Durum
**TAMAMLANDI**

## Yapılanlar
- S3 / MinIO destekli `StorageService` (`apps/api/core/storage.py`) entegre edildi ve bucket oluşturma mantığı aktifleştirildi.
- S3 Object Key formatı kurala uygun şekilde ayarlandı (`tenant_id/matter_id/document_id.pdf`).
- `apps/api/routers/documents.py` içerisindeki routerlar düzenlendi. 
  - `POST /documents/upload-intent` MinIO'dan pre-signed URL dönüyor.
  - `POST /documents/{document_id}/complete` ile yükleme bittiğinde ClamAV taraması kuyruğa (Queue) atılıyor.
  - `GET /documents/{document_id}/download` endpoint'i eklendi; dosya temiz (`clean`) olarak işaretlenmişse indirme için S3 pre-signed URL dönüyor.
- `apps/worker/handlers/document.py` içerisinde `handle_scan_document` oluşturuldu. `SCAN_DOCUMENT` işi tetiklendiğinde S3 üzerinden dosya stream edilerek ClamAV'ye sokulup taratılıyor. Temizse `clean`, değilse `infected` olarak `DocumentRevision.scan_status` veritabanında güncelleniyor.

## Değişen Dosyalar
- `apps/api/routers/documents.py`
- `apps/worker/main.py`
- `apps/worker/handlers/document.py` (Yeni)

## Güvenlik Etkisi
- LocalStorage veya mock indirme yöntemleri kaldırıldı, doğrudan S3 pre-signed URL bazlı erişime geçildi.
- Her dosya indirmeden önce zorunlu olarak ClamAV kontrolünden geçiyor ve virüslü/taranmamış dosyalara HTTP 403 veya 425 döndürülüyor.

## Test Komutları
```bash
docker compose logs legal-api
docker compose logs legal-worker
docker compose logs clamav
```

## Bilinen Eksikler
- Web tarafında `upload-intent` sonrasında `complete` endpointini çağıracak ve dosyanın S3'e doğrudan PUT methodu ile atılmasını sağlayacak kod henüz hazır değil, bu frontend fazında tamamlanacak.

## Sonraki Faz
**Faz 5 — LlamaParse / Unstructured Çevrimdışı İzolasyon**
Doküman içeriğinin text/markdown olarak LlamaParse / Unstructured ile işlenmesi ve queue üzerinden yürütülmesi.
