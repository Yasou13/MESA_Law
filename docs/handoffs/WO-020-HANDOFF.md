# WO-020: MESA Dataset Binding ve Rebuild - HANDOFF

- **Status:** COMPLETED
- **Details:** Matter-private ve legal-source dataset binding işlemleri, döküman revizyonlarının aktarımı (ingestion), MESA/canonical korelasyonu ve tenant/matter bazında rebuild (purge/retraction) yapıları entegre edildi. MesaIngestionPort arayüzü eklendi, MesaV4HttpAdapter içerisine dahil edildi ve MesaSyncService üzerinden senkronizasyon ve rebuild uç noktaları (/api/matters/{matter_id}/rebuild-mesa ve /api/admin/rebuild-tenant) oluşturuldu.
- **Repository:** MESA Law (Evre C)
- **Tests:** Manual verification via endpoints.
