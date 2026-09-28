# MESA Law - Tam Detaylı Entity ve Field Sözlüğü

Bu dosya, projede bulunan tüm paketlerdeki tüm entity'lerin (veritabanı tablolarının), **ne işe yaradıklarının** ve içerdikleri **her bir alanın (field)** tam ve eksiksiz listesidir.

## Paket: `audit`

### `AuditEvent`
**Sınıfın İşlevi:** Sistemdeki standart eylemlerin (okuma, yazma, silme) denetim günlüğüdür.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`userId`** (`String`): Kullanıcı (User) ID'si.
* **`action`** (`String`): Bu alanın değeri.
* **`entityType`** (`String`): Bu alanın değeri.
* **`entityId`** (`String`): Bağlı olduğu entity kaydının ID'si.
* **`changes`** (`String`): Bu alanın değeri.
* **`timestamp`** (`OffsetDateTime`): Bu alanın değeri.

### `LegalAuditLog`
**Sınıfın İşlevi:** Yasal zorunluluk gereği tutulan daha sıkı denetim kayıtlarıdır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`userId`** (`String`): Kullanıcı (User) ID'si.
* **`action`** (`String`): Bu alanın değeri.
* **`entityType`** (`String`): Bu alanın değeri.
* **`entityId`** (`String`): Bağlı olduğu entity kaydının ID'si.
* **`details`** (`String`): Bu alanın değeri.
* **`ipAddress`** (`String`): Bu alanın değeri.

### `Notification`
**Sınıfın İşlevi:** Kullanıcılara gönderilen sistem içi bildirimlerdir.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`userId`** (`String`): Kullanıcı (User) ID'si.
* **`title`** (`String`): Başlık.
* **`message`** (`String`): Mesaj içeriği.
* **`category`** (`String`): Bu alanın değeri.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`timestamp`** (`OffsetDateTime`): Bu alanın değeri.

## Paket: `auth`

### `Firm`
**Sınıfın İşlevi:** Sistemi kullanan hukuk bürolarıdır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`name`** (`String`): İsim / Ad.

### `Membership`
**Sınıfın İşlevi:** Kullanıcıların hangi büroda hangi yetkiyle çalıştığını bağlar.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`userId`** (`String`): Kullanıcı (User) ID'si.
* **`firmId`** (`String`): Hukuk bürosu (Firm) ID'si.
* **`role`** (`Role`): Üstlendiği rol veya yetki seviyesi.
* **`active`** (`boolean`): Kayıt/Üyelik aktif mi?
* **`user`** (`User`): Bu alanın değeri.
* **`firm`** (`Firm`): Bu alanın değeri.

### `Role`
**Sınıfın İşlevi:** Kullanıcının büro içindeki yetki rolleridir.

**Enum Seçenekleri:**
* `FIRM_ADMIN`
* `ATTORNEY`
* `PARALEGAL`
* `READ_ONLY`
* `AUDITOR`
* `SUPPORT_TEMPORARY`

### `User`
**Sınıfın İşlevi:** Sisteme giriş yapan gerçek kişi/avukatlardır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`email`** (`String`): E-posta adresi.
* **`keycloakId`** (`String`): Kimlik doğrulama sunucusundaki (Keycloak) benzersiz kullanıcı ID'si.
* **`fullName`** (`String`): Kişinin tam adı.
* **`supportAccessGranted`** (`boolean`): Bu alanın değeri.
* **`supportAccessGrantedUntil`** (`OffsetDateTime`): Bu alanın değeri.

## Paket: `base`

### `BaseEntity`
**Sınıfın İşlevi:** Bütün tabloların ortak atasıdır. ID, oluşturulma zamanı ve silinme durumunu tutar.

**İçerdiği Alanlar (Fields):**
* **`id`** (`String`): Benzersiz kayıt kimliği (UUIDv7).
* **`createdAt`** (`OffsetDateTime`): Kaydın oluşturulma zamanı.
* **`updatedAt`** (`OffsetDateTime`): Kaydın son güncellenme zamanı.
* **`createdBy`** (`String`): Kaydı oluşturan kullanıcının ID'si.
* **`updatedBy`** (`String`): Kaydı son güncelleyen kullanıcının ID'si.
* **`versionId`** (`Integer`): Aynı anda güncellemeleri (çakışmaları) önlemek için versiyon numarası (Optimistic Locking).
* **`deleted`** (`boolean`): Soft-delete durumu. True ise kayıt silinmiş (çöp kutusunda) kabul edilir.
* **`deletedAt`** (`OffsetDateTime`): Kaydın silinme tarihi.
* **`legalHold`** (`boolean`): Yasal nedenlerle bu kaydın veritabanından kalıcı olarak silinmesini engelleyen kilit.

### `TenantAwareEntity`
**Sınıfın İşlevi:** Sistemi çok kiracılı (multi-tenant) yapan yapıdır. Hangi büroya ait olduğunu tutar.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`tenant`** (`Firm`): Bu alanın değeri.

## Paket: `deadline`

### `ApprovedDeadline`
**Sınıfın İşlevi:** Avukat tarafından onaylanıp takvime kesin olarak işlenen resmi sürelerdir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`deadlineCandidateId`** (`String`): Onaylanan taslak sürenin ID'si.
* **`dueDate`** (`LocalDate`): Son tarih.
* **`timezone`** (`String`): Saat dilimi (Genelde Europe/Istanbul).
* **`description`** (`String`): Detaylı açıklama metni.
* **`completed`** (`boolean`): Süre tamamlandı / İş yapıldı mı?

### `DeadlineCandidate`
**Sınıfın İşlevi:** Yapay zekanın evrak okuyarak tespit ettiği taslak/öneri sürelerdir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`ruleId`** (`String`): Tetiklenen kuralın ID'si.
* **`triggerEvent`** (`String`): Süreyi tetikleyen olayın açıklaması.
* **`triggerDate`** (`LocalDate`): Tetikleyici olayın tarihi (Tebligat tarihi vb.).
* **`calculationTrace`** (`String`): Yapay zekanın bu süreyi nasıl hesapladığının adım adım açıklaması (JSON).
* **`calculatedDate`** (`LocalDate`): Hesaplanan son gün.
* **`description`** (`String`): Detaylı açıklama metni.
* **`status`** (`DeadlineState`): Mevcut durum veya aşama.
* **`confidenceScore`** (`Double`): Yapay zekanın doğruluk güven skoru (0-1 arası).
* **`timezone`** (`String`): Saat dilimi (Genelde Europe/Istanbul).

### `DeadlineRule`
**Sınıfın İşlevi:** Sistemdeki hukuki süre hesaplama kurallarıdır (Örn: HMK 127).

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`ruleName`** (`String`): Kuralın adı (Örn: HMK 127 Cevap Süresi).
* **`description`** (`String`): Detaylı açıklama metni.
* **`jurisdiction`** (`String`): Yargı çevresi veya mahkeme.
* **`procedureType`** (`String`): Usul türü (Yazılı yargılama, Basit yargılama).
* **`triggerType`** (`String`): Süreyi başlatan tetikleyici eylem (Tebliğ, Karar vb.).
* **`duration`** (`int`): Sürenin uzunluğu (Sayı).
* **`durationUnit`** (`String`): Sürenin birimi (Gün, Hafta, Ay).
* **`calculationMethod`** (`String`): Hesaplama yöntemi (Takvim günü, İş günü).
* **`effectiveFrom`** (`OffsetDateTime`): Kuralın yürürlüğe giriş tarihi.
* **`effectiveTo`** (`OffsetDateTime`): Kuralın yürürlükten kalkış tarihi (Mülga kanunlar için).
* **`legalSourceId`** (`String`): Kuralın dayandığı kanun maddesinin ID'si.
* **`holidayCalendarVersion`** (`String`): Tatil günleri takviminin versiyonu (Adli tatil hesaplaması için).
* **`reviewedBy`** (`String`): Kuralı inceleyen/onaylayan hukukçunun ID'si.
* **`rulePackVersion`** (`String`): Kural paketinin versiyonu.

### `DeadlineState`
**Sınıfın İşlevi:** Sürenin hangi aşamada olduğunu gösterir.

**Enum Seçenekleri:**
* `POTENTIAL_DEADLINE`
* `RULE_MATCHED`
* `CALCULATED`
* `ATTORNEY_VERIFIED`
* `SCHEDULED`
* `REJECTED`

## Paket: `document`

### `Document`
**Sınıfın İşlevi:** Sisteme yüklenen belgenin genel/mantıksal tanımıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`title`** (`String`): Başlık.
* **`revisions`** (`List<DocumentRevision>`): Bu alanın değeri.

### `DocumentChunk`
**Sınıfın İşlevi:** Yapay zekanın okuyabilmesi için belgenin ayrıştırılmış küçük paragraf parçacıklarıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`revisionId`** (`String`): Bağlı olduğu doküman revizyonunun (versiyonunun) ID'si.
* **`pageId`** (`String`): Sayfa ID'si.
* **`chunkIndex`** (`int`): Parçanın (Chunk) sayfa veya belge içindeki sırası.
* **`chunkType`** (`String`): Parçanın tipi (paragraf, tablo vb.).
* **`textContent`** (`String`): Çıkarılan saf metin içeriği.
* **`watermarkedText`** (`String`): Filigran eklenmiş metin.
* **`characterStart`** (`Integer`): Metnin başladığı karakter sırası (index).
* **`characterEnd`** (`Integer`): Metnin bittiği karakter sırası (index).
* **`contentSha256`** (`String`): Sadece bu metin parçasının SHA-256 özeti.
* **`extractionVersion`** (`String`): Veriyi çıkaran yapay zeka modelinin/algoritmasının versiyonu.
* **`provenanceState`** (`String`): İzlenebilirlik durumu (Zayıf/Güçlü kanıt).
* **`bbox`** (`String`): Sayfa üzerindeki X-Y koordinatları (Kırmızı kutu çizmek için - Bounding Box).

### `DocumentRevision`
**Sınıfın İşlevi:** Belgenin güncellendikçe değişen fiziksel versiyonlarıdır (S3 dosyası).

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`version`** (`int`): Versiyon / Sürüm numarası.
* **`quarantineKey`** (`String`): Virüs taramasında karantinaya alınan dosyanın bulut adresi.
* **`s3Key`** (`String`): Orijinal dosyanın bulut depolamadaki (S3/MinIO) şifreli adresi.
* **`canonical`** (`boolean`): Bu versiyonun, belgenin ana (geçerli) versiyonu olup olmadığı.
* **`immutableAt`** (`OffsetDateTime`): Dosyanın değiştirilemez (Legal Hold/WORM) hale geldiği tarih.
* **`failureReason`** (`String`): İşlem/Tarama başarısız olduysa sebebi.
* **`fileHash`** (`String`): Dosyanın SHA-256 kriptografik özeti (Değiştirilmediğinin kanıtı).
* **`sizeBytes`** (`Integer`): Dosya boyutu (Byte).
* **`mimeType`** (`String`): Dosya formatı (application/pdf vb.).
* **`scanStatus`** (`DocumentState`): Virüs tarama ve işleme durumu.
* **`document`** (`Document`): Bu alanın değeri.

### `DocumentState`
**Sınıfın İşlevi:** Belgenin geçirdiği işlem aşamalarıdır.

**Enum Seçenekleri:**
* `UPLOAD_INTENT_CREATED`
* `UPLOADING`
* `UPLOADED`
* `VERIFYING`
* `QUARANTINED`
* `SCANNING`
* `CLEAN`
* `INFECTED`
* `PARSING`
* `OCR_REQUIRED`
* `OCR_RUNNING`
* `PARSED`
* `EXTRACTION_PENDING`
* `READY`
* `FAILED`
* `BLOCKED`
* `MANUAL_REVIEW_REQUIRED`

### `ParsedDocument`
**Sınıfın İşlevi:** Belgenin ham metne dönüştürülmüş genel kaydıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`revisionId`** (`String`): Bağlı olduğu doküman revizyonunun (versiyonunun) ID'si.
* **`parsingRevision`** (`int`): Belgenin kaçıncı kez dönüştürüldüğü (parse edildiği).
* **`parserUsed`** (`String`): Dönüştürme işleminde kullanılan araç (PyMuPDF, Tesseract vb.).
* **`ocrVersion`** (`String`): OCR motorunun versiyonu.
* **`pipelineVersion`** (`String`): Veri işleme hattının versiyonu.
* **`inputHash`** (`String`): İşleme giren verinin özeti.
* **`outputHash`** (`String`): İşlemden çıkan verinin özeti.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`provenanceState`** (`String`): İzlenebilirlik durumu (Zayıf/Güçlü kanıt).
* **`pages`** (`List<ParsedPage>`): Bu alanın değeri.

### `ParsedPage`
**Sınıfın İşlevi:** Dönüştürülmüş belgenin sayfa bazlı metinleri ve koordinatlarıdır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`parsedDocumentId`** (`String`): Bağlı olduğu dönüştürülmüş doküman kaydının ID'si.
* **`pageNumber`** (`int`): Orijinal belgedeki sayfa numarası.
* **`textContent`** (`String`): Çıkarılan saf metin içeriği.
* **`layoutData`** (`String`): Sayfanın görsel düzen (layout) bilgileri (JSON).
* **`parsedDocument`** (`ParsedDocument`): Bu alanın değeri.

### `SourceLocator`
**Sınıfın İşlevi:** Yapay zekanın çıkardığı bir bilginin orijinal belgedeki kesin koordinat (kanıt) adresidir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`documentRevisionId`** (`String`): Bağlı olduğu doküman versiyonunun ID'si.
* **`parsedDocumentId`** (`String`): Bağlı olduğu dönüştürülmüş doküman kaydının ID'si.
* **`parsedPageId`** (`String`): Bağlı olduğu dönüştürülmüş sayfanın ID'si.
* **`chunkId`** (`String`): Bağlı olduğu metin parçasının (Chunk) ID'si.
* **`pageNumber`** (`int`): Orijinal belgedeki sayfa numarası.
* **`paragraphIndex`** (`Integer`): Sayfadaki paragraf sırası.
* **`blockIndex`** (`Integer`): Sayfadaki görsel blok sırası.
* **`characterStart`** (`Integer`): Metnin başladığı karakter sırası (index).
* **`characterEnd`** (`Integer`): Metnin bittiği karakter sırası (index).
* **`bboxX0`** (`Double`): X Ekseni başlangıç koordinatı.
* **`bboxY0`** (`Double`): Y Ekseni başlangıç koordinatı.
* **`bboxX1`** (`Double`): X Ekseni bitiş koordinatı.
* **`bboxY1`** (`Double`): Y Ekseni bitiş koordinatı.
* **`textSnippet`** (`String`): Kanıt olarak kırpılan kısa metin alıntısı.
* **`textHash`** (`String`): Alıntının SHA-256 özeti.
* **`evidenceText`** (`String`): Delil niteliğindeki tam metin.
* **`evidenceSha256`** (`String`): Delil metninin özeti.
* **`parserVersion`** (`String`): Bu alanın değeri.
* **`ocrVersion`** (`String`): OCR motorunun versiyonu.
* **`extractionVersion`** (`String`): Veriyi çıkaran yapay zeka modelinin/algoritmasının versiyonu.
* **`provenanceState`** (`String`): İzlenebilirlik durumu (Zayıf/Güçlü kanıt).
* **`verifiedAt`** (`OffsetDateTime`): Avukat tarafından doğrulanma tarihi.

## Paket: `draft`

### `Draft`
**Sınıfın İşlevi:** Sistem üzerinden AI yardımıyla yazılan dilekçe taslağının kendisidir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`title`** (`String`): Başlık.
* **`content`** (`String`): İçerik (Metin, HTML veya JSON).
* **`version`** (`int`): Versiyon / Sürüm numarası.
* **`etag`** (`String`): Versiyonlama ve önbellek (cache) kontrolü için ETag.
* **`status`** (`String`): Mevcut durum veya aşama.

### `DraftCitation`
**Sınıfın İşlevi:** Dilekçe taslağına eklenen kanıt/atıf bağlantılarıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`draftId`** (`String`): Bağlı olduğu taslağın ID'si.
* **`draftRevisionId`** (`String`): Bağlı olduğu taslak versiyonunun ID'si.
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`documentRevisionId`** (`String`): Bağlı olduğu doküman versiyonunun ID'si.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).
* **`citationText`** (`String`): Atıf metni (Örn: Yargıtay 9. HD...).
* **`verificationState`** (`String`): Atıfın doğrulanma durumu.

### `DraftRevision`
**Sınıfın İşlevi:** Yazılmakta olan dilekçenin eski versiyonlarıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`draftId`** (`String`): Bağlı olduğu taslağın ID'si.
* **`version`** (`int`): Versiyon / Sürüm numarası.
* **`content`** (`String`): İçerik (Metin, HTML veya JSON).
* **`changeSummary`** (`String`): Bu versiyonda yapılan değişikliklerin özeti.

## Paket: `matter`

### `Claim`
**Sınıfın İşlevi:** Davaya konu olan hukuki iddialardır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`claimantPartyId`** (`String`): İddia eden tarafın ID'si.
* **`defendantPartyId`** (`String`): İddia edilen / Savunan tarafın ID'si.
* **`description`** (`String`): Detaylı açıklama metni.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`reviewStatus`** (`String`): İnceleme / Onay durumu.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).

### `ClaimEvidenceLink`
**Sınıfın İşlevi:** İddiaları, onları destekleyen delillerle eşleştiren köprü tablosudur.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`claimId`** (`String`): Bağlı olduğu iddianın ID'si.
* **`evidenceId`** (`String`): Bağlı olduğu delilin ID'si.
* **`supportType`** (`String`): Delilin iddiayı destekleme yönü (Destekler, Çürütür).

### `ConflictCheckResult`
**Sınıfın İşlevi:** Yeni dava öncesi taraflar arasında çıkar çatışması olup olmadığını gösteren rapordur.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`requestedBy`** (`String`): Talebi oluşturan kişinin ID'si.
* **`partyNames`** (`String`): Çıkar çatışması kontrolü için girilen taraf isimleri (JSON).
* **`hasConflicts`** (`boolean`): Çıkar çatışması bulundu mu?
* **`results`** (`String`): İşlem/Kontrol sonuçları (JSON).
* **`status`** (`String`): Mevcut durum veya aşama.

### `EvidenceItem`
**Sınıfın İşlevi:** Davada delil olarak sunulan materyallerdir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`description`** (`String`): Detaylı açıklama metni.
* **`reviewStatus`** (`String`): İnceleme / Onay durumu.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).

### `Matter`
**Sınıfın İşlevi:** Bir dava dosyası veya hukuki işin ana merkezidir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`title`** (`String`): Başlık.
* **`internalReference`** (`String`): Büronun kendi iç dosya/referans numarası.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`clientName`** (`String`): Müvekkilin adı.
* **`responsibleAttorneyId`** (`String`): Dosyadan sorumlu olan baş avukatın ID'si.
* **`jurisdiction`** (`String`): Yargı çevresi veya mahkeme.
* **`caseType`** (`String`): Dava/İş türü (Ceza, İş, Ticaret vb.).
* **`confidentialityLevel`** (`String`): Gizlilik derecesi (Sadece yetkili avukatlar görebilsin diye).
* **`aiProcessingPolicy`** (`String`): Bu dosya için yapay zeka işleme politikası (standart, katı vb.).
* **`openedAt`** (`OffsetDateTime`): Açılış tarihi.
* **`closedAt`** (`OffsetDateTime`): Kapanış tarihi.

### `MatterEvent`
**Sınıfın İşlevi:** Dava takvimindeki (kronolojideki) önemli olaylardır (duruşma vb.).

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`eventType`** (`String`): Olayın türü (Duruşma, Tebligat vb.).
* **`description`** (`String`): Detaylı açıklama metni.
* **`eventDate`** (`OffsetDateTime`): Olayın gerçekleştiği tarih.
* **`datePrecision`** (`String`): Tarihin kesinlik derecesi (Gün, Ay, Yıl).
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).
* **`reviewState`** (`String`): Avukat inceleme durumu (Önerildi, Onaylandı, Reddedildi).
* **`sourceType`** (`String`): Bilginin kaynağı (Yapay zeka bulduysa document, elle girildiyse manual).
* **`confidence`** (`String`): Yapay zekanın bu bilgiyi çıkarırken duyduğu güven seviyesi (high, low vb.).

### `MatterMember`
**Sınıfın İşlevi:** Hangi avukatın hangi dava dosyasına erişim yetkisi olduğunu belirler.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`userId`** (`String`): Kullanıcı (User) ID'si.
* **`accessScope`** (`String`): Kullanıcının bu dosyadaki yetki kapsamı (read, write, admin).

### `MatterParty`
**Sınıfın İşlevi:** Davadaki taraflardır (Davacı, Davalı).

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`name`** (`String`): İsim / Ad.
* **`role`** (`String`): Üstlendiği rol veya yetki seviyesi.
* **`type`** (`String`): Tip / Kategori.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).

## Paket: `mesa`

### `MesaScopeBinding`
**Sınıfın İşlevi:** Dava dosyasının, ana yapay zeka (MESA Core) sistemindeki çalışma alanına bağlantısıdır.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`mesaTenantId`** (`String`): Bağlı olduğu mesaTenant kaydının ID'si.
* **`workspaceId`** (`String`): Bağlı olduğu workspace kaydının ID'si.
* **`datasetId`** (`String`): Bağlı olduğu dataset kaydının ID'si.
* **`agentId`** (`String`): Bağlı olduğu agent kaydının ID'si.
* **`provisioningStatus`** (`String`): Bu alanın değeri.
* **`lastVerifiedAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`lastError`** (`String`): Bu alanın değeri.

### `MesaSyncRecord`
**Sınıfın İşlevi:** Onaylanan verilerin ana yapay zeka ile başarıyla senkronize edilip edilmediğinin logudur.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`bindingId`** (`String`): Bağlı olduğu binding kaydının ID'si.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).
* **`assertionId`** (`String`): Bağlı olduğu assertion kaydının ID'si.
* **`resourceType`** (`String`): Bu alanın değeri.
* **`resourceId`** (`String`): Bağlı olduğu resource kaydının ID'si.
* **`idempotencyKey`** (`String`): Bu alanın değeri.
* **`payloadHash`** (`String`): Bu alanın değeri.
* **`requestPayload`** (`String`): Bu alanın değeri.
* **`mutationId`** (`String`): Bağlı olduğu mutation kaydının ID'si.
* **`candidateId`** (`String`): Bağlı olduğu candidate kaydının ID'si.
* **`pipelineRunId`** (`String`): Bağlı olduğu pipelineRun kaydının ID'si.
* **`sessionId`** (`String`): Bağlı olduğu session kaydının ID'si.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`terminal`** (`boolean`): Bu alanın değeri.
* **`attempts`** (`int`): Bu alanın değeri.
* **`lastError`** (`String`): Bu alanın değeri.
* **`lastPolledAt`** (`OffsetDateTime`): Bu alanın değeri.

## Paket: `queue`

### `Job`
**Sınıfın İşlevi:** Arka planda (Worker) çalışacak işlemlerin listesidir.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`type`** (`String`): Tip / Kategori.
* **`payload`** (`String`): İşlenecek verinin içeriği (JSON).
* **`status`** (`JobStatus`): Mevcut durum veya aşama.
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`maxRetries`** (`int`): Bu alanın değeri.
* **`retries`** (`int`): Bu alanın değeri.
* **`attemptsMade`** (`int`): Bu alanın değeri.
* **`runAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`lockedAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`lockedUntil`** (`OffsetDateTime`): Bu alanın değeri.
* **`heartbeatAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`leaseToken`** (`String`): Bu alanın değeri.
* **`requestedBy`** (`String`): Talebi oluşturan kişinin ID'si.
* **`idempotencyKey`** (`String`): Bu alanın değeri.
* **`errorMessage`** (`String`): Bu alanın değeri.
* **`errorClass`** (`String`): Bu alanın değeri.
* **`attempts`** (`List<JobAttempt>`): Bu alanın değeri.

### `JobAttempt`
**Sınıfın İşlevi:** Arka plan işinin kaçıncı kez denendiği ve hata loglarını tutar.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`jobId`** (`String`): Bağlı olduğu job kaydının ID'si.
* **`attemptNumber`** (`int`): İşlemin kaçıncı kez denendiği.
* **`startedAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`finishedAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`status`** (`String`): Mevcut durum veya aşama.
* **`errorDetails`** (`String`): Bu alanın değeri.
* **`leaseToken`** (`String`): Bu alanın değeri.
* **`job`** (`Job`): Bu alanın değeri.

### `JobStatus`
**Sınıfın İşlevi:** İşin mevcut durumu.

**Enum Seçenekleri:**
* `PENDING`
* `RUNNING`
* `SUCCEEDED`
* `FAILED`
* `DEAD`

### `Outbox`
**Sınıfın İşlevi:** Servisler arası mesajlaşmayı güvenli hale getiren giden kutusudur.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`eventType`** (`String`): Olayın türü (Duruşma, Tebligat vb.).
* **`payload`** (`String`): İşlenecek verinin içeriği (JSON).
* **`status`** (`String`): Mevcut durum veya aşama.

## Paket: `research`

### `LegalSource`
**Sınıfın İşlevi:** Araştırma yapılan spesifik bir yasa maddesi veya karardır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`sourcePackageId`** (`String`): Bağlı olduğu sourcePackage kaydının ID'si.
* **`title`** (`String`): Başlık.
* **`citation`** (`String`): Bu alanın değeri.
* **`content`** (`String`): İçerik (Metin, HTML veya JSON).
* **`sourceType`** (`String`): Bilginin kaynağı (Yapay zeka bulduysa document, elle girildiyse manual).
* **`jurisdiction`** (`String`): Yargı çevresi veya mahkeme.
* **`court`** (`String`): Bu alanın değeri.
* **`chamber`** (`String`): Bu alanın değeri.
* **`decisionNumber`** (`String`): Bu alanın değeri.
* **`decisionDate`** (`OffsetDateTime`): Bu alanın değeri.
* **`effectiveFrom`** (`OffsetDateTime`): Kuralın yürürlüğe giriş tarihi.
* **`effectiveTo`** (`OffsetDateTime`): Kuralın yürürlükten kalkış tarihi (Mülga kanunlar için).
* **`status`** (`String`): Mevcut durum veya aşama.
* **`licenseType`** (`String`): Bu alanın değeri.
* **`snapshotId`** (`String`): Bağlı olduğu snapshot kaydının ID'si.
* **`contentHash`** (`String`): Bu alanın değeri.

### `SourcePackage`
**Sınıfın İşlevi:** İçtihat, mevzuat gibi dış kaynak veri paketleridir.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`name`** (`String`): İsim / Ad.
* **`description`** (`String`): Detaylı açıklama metni.
* **`version`** (`String`): Versiyon / Sürüm numarası.

## Paket: `review`

### `ExtractionSuggestion`
**Sınıfın İşlevi:** Yapay zekanın belge okuyarak avukata sunduğu ham çıkarım önerileridir.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`documentId`** (`String`): Bağlı olduğu dokümanın ID'si.
* **`documentRevisionId`** (`String`): Bağlı olduğu doküman versiyonunun ID'si.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).
* **`suggestionType`** (`String`): Bu alanın değeri.
* **`payload`** (`String`): İşlenecek verinin içeriği (JSON).
* **`extractorName`** (`String`): Bu alanın değeri.
* **`extractorVersion`** (`String`): Bu alanın değeri.
* **`promptVersion`** (`String`): Bu alanın değeri.
* **`parserVersion`** (`String`): Bu alanın değeri.
* **`confidenceCategory`** (`String`): Bu alanın değeri.
* **`reviewState`** (`String`): Avukat inceleme durumu (Önerildi, Onaylandı, Reddedildi).
* **`idempotencyKey`** (`String`): Bu alanın değeri.

### `LegalAssertion`
**Sınıfın İşlevi:** Avukat tarafından onaylanıp kesinleşen ve yapay zekaya öğretilen hukuki gerçekliktir.

> Bu sınıf **`TenantAwareEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`claimId`** (`String`): Bağlı olduğu iddianın ID'si.
* **`evidenceId`** (`String`): Bağlı olduğu delilin ID'si.
* **`legalSourceId`** (`String`): Kuralın dayandığı kanun maddesinin ID'si.
* **`assertionText`** (`String`): Bu alanın değeri.
* **`sourceLocatorId`** (`String`): Bu bilginin kanıtı olan orijinal belgedeki koordinat adresi (SourceLocator).
* **`reviewId`** (`String`): Bağlı olduğu review kaydının ID'si.
* **`reviewVersion`** (`Integer`): Bu alanın değeri.
* **`reviewStatus`** (`String`): İnceleme / Onay durumu.
* **`assertionType`** (`String`): Bu alanın değeri.
* **`subjectText`** (`String`): Bu alanın değeri.
* **`predicate`** (`String`): Bu alanın değeri.
* **`objectText`** (`String`): Bu alanın değeri.
* **`objectData`** (`String`): Bu alanın değeri.
* **`polarity`** (`String`): Bu alanın değeri.
* **`modality`** (`String`): Bu alanın değeri.
* **`canonicalStatus`** (`String`): Bu alanın değeri.
* **`publicationStatus`** (`String`): Bu alanın değeri.

### `ReviewItem`
**Sınıfın İşlevi:** Yapay zekanın çıkardığı bilgilerin avukata sunulduğu onay/inceleme ekranı kaydıdır.

> Bu sınıf **`BaseEntity`** sınıfından miras alır (O sınıftaki tüm alanları otomatik olarak içerir).

**İçerdiği Alanlar (Fields):**
* **`tenantId`** (`String`): Kaydın ait olduğu hukuk bürosunun (Firm) ID'si. Veri yalıtımı (RLS) için kullanılır.
* **`matterId`** (`String`): Bağlı olduğu dava/iş dosyasının (Matter) ID'si.
* **`entityType`** (`String`): Bu alanın değeri.
* **`entityId`** (`String`): Bağlı olduğu entity kaydının ID'si.
* **`suggestionId`** (`String`): Bağlı olduğu suggestion kaydının ID'si.
* **`proposedContent`** (`String`): Bu alanın değeri.
* **`status`** (`ReviewState`): Mevcut durum veya aşama.
* **`externalUseReadyAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`reviewedBy`** (`String`): Kuralı inceleyen/onaylayan hukukçunun ID'si.
* **`reviewedAt`** (`OffsetDateTime`): Bu alanın değeri.
* **`correctedContent`** (`String`): Bu alanın değeri.
* **`decisionReason`** (`String`): Bu alanın değeri.

### `ReviewState`
**Sınıfın İşlevi:** İnceleme kaydının onay/ret durumudur.

**Enum Seçenekleri:**
* `PROPOSED`
* `APPROVED`
* `CORRECTED`
* `REJECTED`
* `PUBLISHING`
* `PUBLISHED`
* `PUBLICATION_FAILED`

