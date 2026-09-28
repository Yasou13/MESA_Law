import os
import re

base_dir = r'c:\Users\mehmet\Desktop\MESA_Law\apps\api-java\src\main\java\com\mesalaw\entity'
output_file = r'c:\Users\mehmet\.gemini\antigravity-ide\brain\f4f98681-0392-45bb-a8eb-309e78bb6aff\full_entities_dictionary.md'

explanations = {
    'id': 'Benzersiz kayýt kimliði (UUIDv7).',
    'createdAt': 'Kaydýn oluþturulma zamaný.',
    'updatedAt': 'Kaydýn son güncellenme zamaný.',
    'createdBy': 'Kaydý oluþturan kullanýcýnýn ID\\'si.',
    'updatedBy': 'Kaydý son güncelleyen kullanýcýnýn ID\\'si.',
    'versionId': 'Ayný anda güncellemeleri (çakýþmalarý) önlemek için versiyon numarasý (Optimistic Locking).',
    'deleted': 'Soft-delete durumu. True ise kayýt silinmiþ (çöp kutusunda) kabul edilir.',
    'deletedAt': 'Kaydýn silinme tarihi.',
    'legalHold': 'Yasal nedenlerle bu kaydýn veritabanýndan kalýcý olarak silinmesini engelleyen kilit.',
    'tenantId': 'Kaydýn ait olduðu hukuk bürosunun (Firm) ID\\'si. Veri yalýtýmý (RLS) için kullanýlýr.',
    'matterId': 'Baðlý olduðu dava/iþ dosyasýnýn (Matter) ID\\'si.',
    'documentId': 'Baðlý olduðu dokümanýn ID\\'si.',
    'revisionId': 'Baðlý olduðu doküman revizyonunun (versiyonunun) ID\\'si.',
    'userId': 'Kullanýcý (User) ID\\'si.',
    'firmId': 'Hukuk bürosu (Firm) ID\\'si.',
    'status': 'Mevcut durum veya aþama.',
    'reviewState': 'Avukat inceleme durumu (Önerildi, Onaylandý, Reddedildi).',
    'description': 'Detaylý açýklama metni.',
    'title': 'Baþlýk.',
    'name': 'Ýsim / Ad.',
    'version': 'Versiyon / Sürüm numarasý.',
    'content': 'Ýçerik (Metin, HTML veya JSON).',
    'confidence': 'Yapay zekanýn bu bilgiyi çýkarýrken duyduðu güven seviyesi (high, low vb.).',
    'confidenceScore': 'Yapay zekanýn doðruluk güven skoru (0-1 arasý).',
    'sourceLocatorId': 'Bu bilginin kanýtý olan orijinal belgedeki koordinat adresi (SourceLocator).',
    'email': 'E-posta adresi.',
    'keycloakId': 'Kimlik doðrulama sunucusundaki (Keycloak) benzersiz kullanýcý ID\\'si.',
    'fullName': 'Kiþinin tam adý.',
    'role': 'Üstlendiði rol veya yetki seviyesi.',
    'active': 'Kayýt/Üyelik aktif mi?',
    'internalReference': 'Büronun kendi iç dosya/referans numarasý.',
    'clientName': 'Müvekkilin adý.',
    'responsibleAttorneyId': 'Dosyadan sorumlu olan baþ avukatýn ID\\'si.',
    'jurisdiction': 'Yargý çevresi veya mahkeme.',
    'caseType': 'Dava/Ýþ türü (Ceza, Ýþ, Ticaret vb.).',
    'confidentialityLevel': 'Gizlilik derecesi (Sadece yetkili avukatlar görebilsin diye).',
    'aiProcessingPolicy': 'Bu dosya için yapay zeka iþleme politikasý (standart, katý vb.).',
    'openedAt': 'Açýlýþ tarihi.',
    'closedAt': 'Kapanýþ tarihi.',
    'accessScope': 'Kullanýcýnýn bu dosyadaki yetki kapsamý (read, write, admin).',
    'type': 'Tip / Kategori.',
    'eventType': 'Olayýn türü (Duruþma, Tebligat vb.).',
    'eventDate': 'Olayýn gerçekleþtiði tarih.',
    'datePrecision': 'Tarihin kesinlik derecesi (Gün, Ay, Yýl).',
    'sourceType': 'Bilginin kaynaðý (Yapay zeka bulduysa document, elle girildiyse manual).',
    'requestedBy': 'Talebi oluþturan kiþinin ID\\'si.',
    'partyNames': 'Çýkar çatýþmasý kontrolü için girilen taraf isimleri.',
    'hasConflicts': 'Çýkar çatýþmasý bulundu mu?',
    'results': 'Ýþlem/Kontrol sonuçlarý (JSON).',
    'claimantPartyId': 'Ýddia eden tarafýn ID\\'si.',
    'defendantPartyId': 'Ýddia edilen / Savunan tarafýn ID\\'si.',
    'reviewStatus': 'Ýnceleme / Onay durumu.',
    'evidenceId': 'Baðlý olduðu delilin ID\\'si.',
    'claimId': 'Baðlý olduðu iddianýn ID\\'si.',
    'supportType': 'Delilin iddiayý destekleme yönü (Destekler, Çürütür).',
    'quarantineKey': 'Virüs taramasýnda karantinaya alýnan dosyanýn bulut adresi.',
    's3Key': 'Orijinal dosyanýn bulut depolamadaki (S3/MinIO) þifreli adresi.',
    'canonical': 'Bu versiyonun, belgenin ana (geçerli) versiyonu olup olmadýðý.',
    'immutableAt': 'Dosyanýn deðiþtirilemez (Legal Hold/WORM) hale geldiði tarih.',
    'failureReason': 'Ýþlem/Tarama baþarýsýz olduysa sebebi.',
    'fileHash': 'Dosyanýn SHA-256 kriptografik özeti (Deðiþtirilmediðinin kanýtý).',
    'sizeBytes': 'Dosya boyutu (Byte).',
    'mimeType': 'Dosya formatý (application/pdf vb.).',
    'scanStatus': 'Virüs tarama ve iþleme durumu.',
    'pageId': 'Sayfa ID\\'si.',
    'chunkIndex': 'Parçanýn (Chunk) sayfa veya belge içindeki sýrasý.',
    'chunkType': 'Parçanýn tipi (paragraf, tablo vb.).',
    'textContent': 'Çýkarýlan saf metin içeriði.',
    'watermarkedText': 'Filigran eklenmiþ metin.',
    'characterStart': 'Metnin baþladýðý karakter sýrasý (index).',
    'characterEnd': 'Metnin bittiði karakter sýrasý (index).',
    'contentSha256': 'Sadece bu metin parçasýnýn SHA-256 özeti.',
    'extractionVersion': 'Veriyi çýkaran yapay zeka modelinin/algoritmasýnýn versiyonu.',
    'provenanceState': 'Ýzlenebilirlik durumu (Zayýf/Güçlü kanýt).',
    'bbox': 'Sayfa üzerindeki X-Y koordinatlarý (Kýrmýzý kutu çizmek için - Bounding Box).',
    'parsingRevision': 'Belgenin kaçýncý kez dönüþtürüldüðü (parse edildiði).',
    'parserUsed': 'Dönüþtürme iþleminde kullanýlan araç (PyMuPDF, Tesseract vb.).',
    'ocrVersion': 'OCR motorunun versiyonu.',
    'pipelineVersion': 'Veri iþleme hattýnýn versiyonu.',
    'inputHash': 'Ýþleme giren verinin özeti.',
    'outputHash': 'Ýþlemden çýkan verinin özeti.',
    'pageNumber': 'Orijinal belgedeki sayfa numarasý.',
    'layoutData': 'Sayfanýn görsel düzen (layout) bilgileri (JSON).',
    'parsedDocumentId': 'Baðlý olduðu dönüþtürülmüþ doküman kaydýnýn ID\\'si.',
    'parsedPageId': 'Baðlý olduðu dönüþtürülmüþ sayfanýn ID\\'si.',
    'chunkId': 'Baðlý olduðu metin parçasýnýn (Chunk) ID\\'si.',
    'paragraphIndex': 'Sayfadaki paragraf sýrasý.',
    'blockIndex': 'Sayfadaki görsel blok sýrasý.',
    'bboxX0': 'X Ekseni baþlangýç koordinatý.',
    'bboxY0': 'Y Ekseni baþlangýç koordinatý.',
    'bboxX1': 'X Ekseni bitiþ koordinatý.',
    'bboxY1': 'Y Ekseni bitiþ koordinatý.',
    'textSnippet': 'Kanýt olarak kýrpýlan kýsa metin alýntýsý.',
    'textHash': 'Alýntýnýn SHA-256 özeti.',
    'evidenceText': 'Delil niteliðindeki tam metin.',
    'evidenceSha256': 'Delil metninin özeti.',
    'verifiedAt': 'Avukat tarafýndan doðrulanma tarihi.',
    'ruleName': 'Kuralýn adý (Örn: HMK 127 Cevap Süresi).',
    'procedureType': 'Usul türü (Yazýlý yargýlama, Basit yargýlama).',
    'triggerType': 'Süreyi baþlatan tetikleyici eylem (Teblið, Karar vb.).',
    'duration': 'Sürenin uzunluðu (Sayý).',
    'durationUnit': 'Sürenin birimi (Gün, Hafta, Ay).',
    'calculationMethod': 'Hesaplama yöntemi (Takvim günü, Ýþ günü).',
    'effectiveFrom': 'Kuralýn yürürlüðe giriþ tarihi.',
    'effectiveTo': 'Kuralýn yürürlükten kalkýþ tarihi (Mülga kanunlar için).',
    'legalSourceId': 'Kuralýn dayandýðý kanun maddesinin ID\\'si.',
    'holidayCalendarVersion': 'Tatil günleri takviminin versiyonu (Adli tatil hesaplamasý için).',
    'reviewedBy': 'Kuralý inceleyen/onaylayan hukukçunun ID\\'si.',
    'rulePackVersion': 'Kural paketinin versiyonu.',
    'ruleId': 'Tetiklenen kuralýn ID\\'si.',
    'triggerEvent': 'Süreyi tetikleyen olayýn açýklamasý.',
    'triggerDate': 'Tetikleyici olayýn tarihi (Tebligat tarihi vb.).',
    'calculationTrace': 'Yapay zekanýn bu süreyi nasýl hesapladýðýnýn adým adým açýklamasý (JSON).',
    'calculatedDate': 'Hesaplanan son gün.',
    'timezone': 'Saat dilimi (Genelde Europe/Istanbul).',
    'deadlineCandidateId': 'Onaylanan taslak sürenin ID\\'si.',
    'dueDate': 'Son tarih.',
    'completed': 'Süre tamamlandý / Ýþ yapýldý mý?',
    'etag': 'Versiyonlama ve önbellek (cache) kontrolü için ETag.',
    'draftId': 'Baðlý olduðu taslaðýn ID\\'si.',
    'changeSummary': 'Bu versiyonda yapýlan deðiþikliklerin özeti.',
    'draftRevisionId': 'Baðlý olduðu taslak versiyonunun ID\\'si.',
    'documentRevisionId': 'Baðlý olduðu doküman versiyonunun ID\\'si.',
    'citationText': 'Atýf metni (Örn: Yargýtay 9. HD...).',
    'verificationState': 'Atýfýn doðrulanma durumu.',
    'message': 'Mesaj içeriði.',
    'payload': 'Ýþlenecek verinin içeriði (JSON).',
    'errorLog': 'Hata logu (Stack trace).',
    'attemptNumber': 'Ýþlemin kaçýncý kez denendiði.',
    'nextRetryAt': 'Bir sonraki deneme zamaný.',
}

def guess_explanation(field_name):
    if field_name in explanations:
        return explanations[field_name]
    # some basic fallbacks
    if field_name.endswith('Id'):
        return f"Baðlý olduðu {field_name[:-2].capitalize()} kaydýnýn ID\\'si."
    if field_name.startswith('is'):
        return f"{field_name[2:]} durumu (Evet/Hayýr)."
    return "Bu alanýn spesifik deðeri."

output = ["# MESA Law - Tam Detaylý Entity ve Field Sözlüðü\n\nBu dosya, projede bulunan tüm paketlerdeki tüm entity'lerin (veritabaný tablolarýnýn) ve içerdikleri **her bir alanýn (field)** tam ve eksiksiz listesidir.\n"]

for root, dirs, files in os.walk(base_dir):
    java_files = [f for f in files if f.endswith('.java')]
    if not java_files:
        continue
        
    pkg_name = os.path.basename(root)
    output.append(f"## Paket: {pkg_name}\n")
    
    for f in java_files:
        filepath = os.path.join(root, f)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Find class name
            class_match = re.search(r'public (?:abstract )?(?:class|enum) (\w+)', content)
            if not class_match:
                continue
            class_name = class_match.group(1)
            
            output.append(f"### {class_name}\n")
            
            # Check if it extends something
            extend_match = re.search(r'public (?:abstract )?class ' + class_name + r' extends (\w+)', content)
            if extend_match:
                parent = extend_match.group(1)
                output.append(f"> Bu sýnýf **{parent}** sýnýfýndan miras alýr (Onun içindeki tüm alanlarý otomatik içerir).\n\n")
                
            # If enum, list values
            if "enum " + class_name in content:
                values = re.findall(r'^\s+([A-Z0-9_]+)', content, re.MULTILINE)
                if values:
                    output.append("**Enum Deðerleri:**\n")
                    for val in values:
                        output.append(f"* {val}\n")
                output.append("\n")
                continue
                
            # Find fields
            fields = re.findall(r'private (\w+(?:<[^>]+>)?(?:\[\])?) (\w+)(?:.*?);', content)
            
            if not fields:
                output.append("*Bu sýnýfa ait özel bir alan bulunmamaktadýr.*\n\n")
            else:
                for field_type, field_name in fields:
                    explanation = guess_explanation(field_name)
                    output.append(f"* **{field_name}** ({field_type}): {explanation}\n")
            output.append("\n")

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('File generated successfully.')
