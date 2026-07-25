## Yapılanlar
- `Job`, `JobAttempt` ve `Outbox` modelleri `apps/api/models/queue.py` altında oluşturuldu. Modeller Alembic ile veritabanına uygulandı.
- PostgreSQL `SKIP LOCKED` özelliğini kullanarak "lease" alabilen, `FOR UPDATE` transaction isolation'ı sağlayan basit ama dayanıklı (durable) bir kuyruk işleyicisi (Worker) `apps/worker/core/queue.py` içine implemente edildi.
- Hata durumunda exponential backoff + deneme (retry) limiti uygulandı, limit aşılınca job'un `dead` durumuna geçmesi (dead-letter queue mantığı) sağlandı.
- İşin bitmeden worker'ın çökmesi durumunda (lease expiration), süresi dolmuş kilitli işleri başka worker'ların alabilmesi için `(Job.locked_until <= now)` mekanizması eklendi.
- Duplicate delivery / crash senaryolarında handler fonksiyonlarının idempotent davranabileceğini doğrulayan testler yazıldı.

## Değişen Dosyalar
- `apps/api/models/queue.py` [NEW]
- `apps/api/models/__init__.py`
- `migrations/versions/130cbd278f22_add_job_and_outbox_models.py` [NEW]
- `apps/worker/core/queue.py` [NEW]
- `apps/worker/test_queue.py` [NEW]
- `docs/work-orders/WO-005.md` [NEW]
- `docs/handoffs/WO-005-HANDOFF.md` [NEW]

## Tasarım Kararları
- RabbitMQ veya Redis yerine PostgreSQL `SKIP LOCKED` seçilerek, "Transactional Outbox" pattern'i ile (aynı veritabanında commit işlemi garantisi) %100 dayanıklılık hedeflendi.
- Worker tasarımı, lock mekanizmasını veritabanına devrettiği için çoklu node/pod mimarisinde eşzamanlı ve çakışmasız çalışabilir.

## Test Sonuçları
- `uv run pytest apps/worker/test_queue.py` başarıyla geçmiştir.
- İşin işlenmesi, fail-and-retry loglaması ve duplicate processing kilitlenme (lease expired) mekanizmaları kusursuz çalışmaktadır.

## Sonraki Önerilen Adım
- WO-006 (Object Storage ve Chain of Custody / Doküman yükleme süreçleri)
