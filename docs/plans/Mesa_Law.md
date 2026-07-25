# MESA Law — Agent-Optimize, Geç MESA Entegrasyonlu Nihai Ürün ve Uygulama Planı

---

## AGENT'A DOĞRUDAN TALİMAT — BU BÖLÜMÜ HER ŞEYDEN ÖNCE OKU

Bu belge tek seferde sana verildi. Aşağıdaki bölümler (1-41 ve "Son değerlendirmem") planın kendisidir — arka plan, ürün kararları ve iş listesi burada. **Bölüm 39 ("Agent-optimize adım adım uygulama planı")** senin operasyon çerçevendir: WO şablonu, Handoff şablonu, agent çalışma ilkeleri (39.1) ve stop condition'lar (39.3) zaten orada tanımlı — onları yeniden yorumlama, olduğu gibi uygula.

### Yürütme Döngüsü (tek seferlik dispatch için bağlayıcı)

1. **WO-000'dan başla**, sırayla ilerle: WO-000 → WO-001 → ... → WO-013 → WO-014 (gap analysis) → WO-015+ (minimum MESA readiness serisi) → WO-019 → WO-020 → ... → WO-027. WO-015+ serisi açık uçlu ("Her generic eksik ayrı work order'dır" — 39.20) — Faz 5 gap analizi (WO-014) sonucunda kaç tane WO-015, WO-016... çıkacağı çalışma sırasında netleşecek; bunları da aynı döngüyle işle, numaralarını kendin sırala ve `docs/work-orders/` altına kaydet.
2. **Her WO için:** a. WO'nun bu belgede tam şablonla mı (WO-000 gibi) yoksa özet madde biçiminde mi (WO-002...WO-013, WO-015+ gibi "Repo/Yapılacaklar/Kabul" özetiyle) tanımlandığını tespit et. Özet biçimindeyse, bölüm 39.2'deki **WO şablonunu** (Amaç/Ön koşullar/İzin verilen yollar/Yasak yollar/Değiştirilecek sözleşmeler/Uygulama adımları/Kabul kriterleri/Çalıştırılacak testler/Güvenlik-veri kontrolü/Rollback/Teslim çıktıları) kendin doldurarak genişlet, önce bunu `docs/work-orders/WO-XXX.md` olarak yaz. b. WO'yu, "İzin verilen repo ve yollar" / "Yasak yollar" sınırları içinde kalarak uygula. c. WO'nun **Kabul kriterleri** ve **Çalıştırılacak testler**ini gerçekten çalıştır — bir sonraki bölümdeki (HALÜSİNASYON KORUMASI) kanıt kuralı olmadan hiçbir kabul kriterini "karşılandı" sayma. d. Bölüm 39.3'teki **stop condition**'lardan biri tetiklenirse (destructive migration, MESA core değişikliği ihtiyacı, iki geçerli mimari alternatif arasında karar gerekliliği, vb.) **dur, kod yazmayı bırak, "nasıl olsa en mantıklısı" diyerek karar verme** — durumu `docs/handoffs/STOP-WO-XXX.md`'ye yaz ve kullanıcıya sor. e. WO tamamlandığında, bölüm 39.2'deki **Handoff şablonu**nu (Yapılanlar/Değişen dosyalar/Tasarım kararları/Test komutları ve sonuçları/Migration etkisi/Güvenlik etkisi/Bilinen eksikler/Rollback/Sonraki önerilen WO) eksiksiz doldurup **ayrı bir dosyaya** yaz: `docs/handoffs/WO-XXX-HANDOFF.md`. Bu adım atlanmadan bir WO "bitti" sayılmaz. f. Handoff yazıldıktan sonra otomatik olarak **bir sonraki WO'ya geç** — ayrı bir onay istemene gerek yok, sadece stop condition veya belirsizlik durumunda dur.
3. Tüm WO'lar (WO-000'dan Faz 10/WO-027'ye ve varsa WO-015+ türevlerine kadar) bitince, `docs/handoffs/` altındaki tüm Handoff dosyalarını tarayıp tek bir `MESA_LAW_ILERLEME_OZETI.md` üret: kaç WO tamamlandı, kaçı blocked/stop condition'da kaldı, hangi testler geçti, bilinen eksikler listesi.

### HALÜSİNASYON KORUMASI (her WO'nun Kabul kriteri/Handoff'undan önce, istisnasız)

- "Kabul kriteri karşılandı" veya "Yapıldı" yazmadan önce kendine sor: _Bunu gerçekten çalıştırıp gördüm mü, yoksa kod mantıken doğru göründüğü için mi varsayıyorum?_ Cevap ikinciyse DURMA, önce çalıştır.
- Yazdığın kodu/migration'ı/config'i, yazdıktan sonra ayrı bir adımda tekrar aç ve gerçekten diskte olduğunu, sözdizimi hatasız olduğunu teyit et.
- "Çalıştırılacak testler" bölümündeki her testi gerçekten çalıştır, çıktısını Handoff'un "Test komutları ve sonuçları" alanına ham hâliyle yapıştır — "testler geçti" demek yeterli değil, komut + çıktı zorunlu.
- Bölüm 39.1 madde 7 zaten yasaklıyor ama tekrar altını çiziyorum: test silmek, assertion zayıflatmak veya skip eklemek bir kabul kriterini karşılamak için kullanılamaz.
- WO-014 (gap analysis) ve türevlerinde ("core değişiklik listesi varsayım değil failing test ile kanıtlanır") — bir MESA core eksikliği iddia ediyorsan mutlaka önce onu tetikleyen failing test'i göster.
- Bir önceki WO'nun Handoff'unda "Bilinen eksikler" olarak işaretlenmiş bir madde varsa ve sıradaki WO ona bağımlıysa, önce o eksiği/riski Handoff'tan oku, yok saymadan ilerleme.

### Oturum Devamlılığı (Resume Protokolü)

Bu plan tek bir kesintisiz oturumda bitmeyecek kadar büyüktür (WO-000'dan WO-027+'ye kadar onlarca çok-dosyalı görev). Bu yüzden **her yeni oturum başında**, herhangi bir WO'ya başlamadan önce şunu yap:

1. `docs/handoffs/` dizinini listele. Hiç dosya yoksa WO-000'dan başla.
2. Varsa, dosya adlarındaki WO numaralarına göre **en yüksek numaralı tamamlanmış** handoff'u bul (bir WO'nun handoff'u varsa ve içinde "Durum: BLOCKED" ya da eksik bölüm yoksa tamamlanmış sayılır).
3. O handoff'un "Sonraki önerilen WO" alanını oku, oradan devam et. Alan boşsa/tutarsızsa, WO numarasına göre bir sonrakine geç.
4. `docs/handoffs/STOP-WO-XXX.md` gibi bir stop-dosyası varsa, önce onu oku — daha önce bir stop condition'da durulmuş ve muhtemelen kullanıcıdan henüz yanıt gelmemiş demektir; aynı WO'yu tekrar en baştan yeniden yapmaya kalkma, önce durumu kullanıcıya hatırlat.
5. Hiçbir zaman zaten tamamlanmış (handoff'u olan) bir WO'yu sessizce tekrar yürütme veya üzerine yeniden yazma — önce mevcut handoff'u oku, hâlâ geçerli mi kontrol et.

### Git / GitHub Kısıtı (mutlak, istisnasız)

- Agent **hiçbir zaman** `git push`, `git remote`, `gh pr create`, `gh pr merge` veya GitHub API'sine yazma yapan başka bir komut çalıştırmaz. Uzak sunucuya (GitHub'a) hiçbir şey gönderilmez.
- Agent **kendi branch'ini açmaz.** Çalışılacak branch kullanıcı tarafından önceden açılıp agent'a bildirilir. Agent ilk iş olarak `git branch --show-current` ile mevcut branch'i doğrular; beklenen branch'te değilse **kod yazmaya başlamadan durur** ve kullanıcıya sorar.
- Agent bu branch üzerinde **yerel commit** atabilir (39.4'teki commit standardını uygula), ama push/PR/merge yok. "39.1 madde 4 — main branch'e doğrudan değişiklik yapılmaz" kuralı zaten bunu destekliyor; ek olarak uzak repoya hiçbir yazma işlemi yapılmaz.
- Bir WO'nun "Teslim çıktıları" veya Handoff şablonu GitHub'a bir şey göndermeyi ima ediyorsa (PR açma gibi), bunu atla ve Handoff'ta "Push/PR: kullanıcı tarafından manuel yapılacak" notunu düş.

### Ortam Ön Koşulu (WO-000'dan önce, zorunlu)

WO-000'daki komutları (`uv sync`, `uv run pytest` vb.) çalıştırmadan önce, ortamın planın 5.3'teki teknoloji yığınını gerçekten çalıştırabildiğini doğrula. Eksik bir araç varsa WO-000'u "BLOCKED — ortam eksik" olarak işaretle, kod yazmaya geçme, kullanıcıya hangi aracın eksik olduğunu bildir.

Kontrol listesi (her biri için gerçek bir komut çalıştırıp çıktısını Handoff'a yapıştır, varsayma):

```
docker --version
docker compose version
uv --version
node --version
pnpm --version
python --version   (MESA ve MESA-Law'ın beklediği sürümle eşleşiyor mu)
```

Ardından 24.1'deki `docker compose --profile core up -d` komutunu çalıştır ve `core` profilindeki servislerin (web, legal-api, legal-worker, postgres, redis, minio, keycloak, clamav, caddy, otel-collector, prometheus, grafana, loki, tempo) hepsinin sağlıklı (healthy/running) duruma geçtiğini doğrula — tek tek durumlarını Handoff'a yapıştır. Bu adım WO-000'un Handoff'unun bir parçası olarak kaydedilir, ayrı bir WO değildir.

### Kısaltılmış WO'larda Yol Kapsamı Kısıtı

WO-002...WO-013 ve WO-015+ gibi bu belgede tam şablonla değil özet madde biçiminde tanımlanan WO'lar için, "İzin verilen repo ve yollar" / "Yasak yollar" alanlarını **kendi inisiyatifinle icat etme** — yalnızca bölüm 23.1 (MESA repo ağacı) ve 23.2 (MESA-Law monorepo ağacı)'de zaten tanımlı dizin/dosya yollarından türet. Bu iki bölümde karşılığı olmayan yeni bir üst düzey dizin/paket oluşturman gerekiyorsa, bu bir mimari genişleme demektir — sessizce ekleme, bunu 39.3'teki stop condition olarak işle ("iki geçerli mimari alternatif arasında karar gerekliliği" kapsamında) ve kullanıcıya sor.

### İsimlendirme Notu

Bu belgede geçen ürün adı **"MESA Legal"/"MESA-Legal" tamamen "MESA Law"/"MESA-Law" olarak değiştirilmiştir** (script ile birebir dönüştürüldü, sonradan yapılan ikinci bir taramada gözden kaçan `https://errors.mesa.legal/...` hata-tipi domain'i de `errors.mesa.law` olarak düzeltildi). İki nokta **bilerek dokunulmadan bırakıldı**, ikisi de aynı ailede — ürün markası değil, çekirdek MESA'nın "Zero-Hallucination Legal Mode"u için önerilen iç sabit/mod adları:

- satır ~138: `MESA_HIGH_ASSURANCE_LEGAL_PROFILE`
- satır ~144: `MESA_LEGAL_REVIEW_PROFILE`

Bunları da `..._LAW_PROFILE`'a çevirmemi ister misin, yoksa MESA çekirdeğinin genel "legal" mod adlandırması (ürün markasından bağımsız, hukuk _domain_'ini ifade eden bir terim) olarak mı kalsın? `legal_mesa_bindings`, `legal_mesa_operations` gibi tablo adlarına ve genel "legal" sözcüğünün geçtiği yüzlerce yere (legal_ontology_versions, Legal Control Panel, vb.) dokunmadım çünkü bunlar ürün markası değil, hukuk domain'inin genel terminolojisi — talebiniz sadece "MESA Legal" marka adının değişmesiydi.

---

ZIP’i yeniden inceleyerek ve güncel hukuk teknolojisi ürünlerini karşılaştırarak vardığım ana sonuç şu:

> **MESA Law, ilk aşamada bir hukuk araştırma veri tabanı, UYAP alternatifi veya genel hukuk chatbotu olmamalı. MESA’nın en güçlü olduğu alana odaklanmalı: özel dava dosyalarını, delilleri, hukuki kaynakları ve büro hafızasını kaynaklarıyla birlikte yöneten “matter intelligence” platformu.**

Harvey veya Legora gibi genel hukuk çalışma alanlarının, Lexis/Westlaw/vLex gibi içerik platformlarının, Spellbook/Luminance gibi sözleşme ürünlerinin ve Clio/Sinerji gibi büro yönetim sistemlerinin tamamını aynı anda kopyalamaya çalışmak ürünü başarısız eder.

> **Nihai agent-optimizasyon revizyonu — 24 Temmuz 2026:** Bu sürümde MESA çekirdeğinin ürün geliştirmesinin başında değil, canonical hukuk uygulaması ve belge pipeline’ı çalıştıktan sonra bağlanması karara bağlandı. MESA-Law ilk aşamada MESA’ya kaynak kodu veya paket bağımlılığı taşımaz; baştan tanımlanan `MesaIntelligencePort`, `MockMesaAdapter` ve PostgreSQL full-text fallback ile geliştirilir. Gerçek MESA V4 adaptörü, contract/gap analizi tamamlandıktan sonra eklenir; MESA core yalnız kanıtlanmış generic capability eksikleri için ve ayrı work order/ADR ile değiştirilir. Ayrıca ID, zaman, transaction, idempotency, concurrency, API hata formatı, auth session, job lease, parser adapter, feature flag, generated client ve agent çalışma protokolü gibi daha önce uygulayıcıya bırakılmış kararlar kesinleştirildi. Uygulama sırası bounded work order’lara bölündü; her agent görevi izin verilen dosyalar, yasak alanlar, testler, çıkış kriteri ve rollback çıktısı taşır.

Doğru ürün sınırı:

```
MESA Law
=
Matter Intelligence
+ Private Legal Memory
+ Evidence & Timeline
+ Source-Grounded Research
+ Draft Verification
+ Human Approval
```

---

# 1. ZIP’e göre MESA’nın gerçek hukuk hazırlık seviyesi

MESA `0.7.0` içinde hukuk uygulaması için güçlü bir altyapı bulunuyor.

## Hazır olan temel

ZIP’te mevcut:

- tenant → workspace → dataset izolasyonu,
- document → immutable revision → source chunk modeli,
- `source_ref` ve `evidence_span`,
- `jurisdiction`,
- `authority_level`,
- `valid_from` ve `valid_to`,
- assertion provenance,
- `CONTRADICTS` ve `SUPERSEDES`,
- SQL/vector/graph projection,
- mutation ledger,
- replay, rollback ve reconciliation,
- Türkçe hukuk çıkarım promptu,
- hukuk odaklı retrieval resolver,
- legal reranking,
- graph poisoning audit,
- çift model doğrulama profili,
- principal ve dataset bazlı erişim.

Bu nedenle sıfırdan bir legal RAG yazmaya gerek yok.

## Ancak hukuk uygulaması henüz yok

Şu kritik parçalar eksik:

- gerçek dosya/matter domain’i,
- PDF/DOCX ingestion,
- OCR,
- sayfa/paragraf/bounding-box provenance,
- belge türü sınıflandırması,
- taraf, iddia, delil ve olay modeli,
- hukuki kaynak kataloğu,
- mevzuat sürüm yönetimi,
- içtihat metadata modeli,
- süre ve tebligat sistemi,
- etik duvar,
- menfaat çatışması kontrolü,
- avukat doğrulama kuyruğu,
- kaynak destekli taslak editörü,
- DOCX/Word entegrasyonu,
- hukuk uygulaması arayüzü,
- resmî veya lisanslı kaynak connector’ları.

Dolayısıyla mevcut sistem:

> **Legal-ready memory engine**

seviyesinde; henüz:

> **Legal application**

seviyesinde değil.

---

# 2. ZIP’te düzeltilmesi gereken hukuk odaklı teknik noktalar

## 2.1 `legal_domain_mode` adı değiştirilmelidir

Kodda bu mod:

```
Zero-Hallucination Legal Mode
```

olarak tanımlanmış.

Bu isim teknik ve hukuki olarak savunulamaz. Hiçbir LLM veya çift model sistemi “sıfır hallucination” garanti edemez.

Yeni ad:

```
MESA_HIGH_ASSURANCE_LEGAL_PROFILE
```

veya:

```
MESA_LEGAL_REVIEW_PROFILE
```

olmalı.

Bu profil şunları ifade etmeli:

- daha sıkı kaynak zorunluluğu,
- schema validation,
- risk bazlı ikinci model,
- düşük güven sonuçlarını review kuyruğuna alma,
- insan onayı olmadan final hukuki çıktı üretmeme.

## 2.2 Hukuk resolver çok dar

Mevcut `LegalEntityResolver` yalnızca yaklaşık olarak:

- TBK,
- TMK,
- TCK,
- HMK,
- TTK,
- üç Yargıtay birimi

üzerinde çalışıyor.

Bu üretim sistemi için yeterli değil.

Hard-coded Python dictionary yerine:

```
legal_ontology_versions
legal_authorities
legal_authority_aliases
courts
court_chambers
jurisdictions
```

tablolarına geçilmeli.

Resolver şu kaynakları kapsamalı:

- Anayasa,
- kanunlar,
- KHK’lar,
- Cumhurbaşkanlığı kararnameleri,
- yönetmelikler,
- tebliğler,
- genelgeler,
- uluslararası sözleşmeler,
- AYM,
- Yargıtay,
- Danıştay,
- BAM/BİM,
- AİHM,
- kurum kararları,
- mevzuat maddeleri,
- geçici maddeler,
- ek maddeler,
- mülga hükümler.

## 2.3 Generic triplet extraction hukuk için yeterli değil

Mevcut prompt:

```
özne — yüklem — nesne
```

üçlüleri üretiyor.

Örneğin:

```
İşveren — feshetti — iş sözleşmesini
```

faydalıdır ama hukuk ürünü için yeterli değildir.

Hukuki extraction aşağıdaki yapıyı üretmeli:

```
{
  "assertion_type": "ALLEGATION",
  "subject": "İşveren",
  "predicate": "TERMINATED",
  "object": "İş sözleşmesi",
  "event_date": "2026-03-14",
  "legal_effect": "employment_termination",
  "source_document_id": "doc_...",
  "page": 4,
  "paragraph": 2,
  "evidence_text": "...",
  "speaker": "Davacı",
  "confidence": 0.91,
  "review_state": "AI_EXTRACTED"
}
```

## 2.4 2.000 karakterlik extraction kesintisi kaldırılmalı

`ingestion_worker.py` içindeki LLM extraction metni yaklaşık 2.000 karakterde kesiyor.

Bu, hukuk belgelerinde ciddi bilgi kaybı oluşturur.

Çözüm:

```
Belge
 ↓
Layout-aware segmentation
 ↓
Başlık/madde/paragraf bazlı chunk
 ↓
Chunk extraction
 ↓
Belge düzeyi reconciliation
```

Belgeyi doğrudan modele vermek yerine önce hukuki belge yapısına göre bölmek gerekir.

## 2.5 Mevcut legal rerank fazla basit

Şu anda kabaca:

```
OFFICIAL           1.15
SUPREME_COURT      1.15
PRIMARY            1.10
SECONDARY          0.95
```

gibi bir çarpan kullanılıyor.

Hukuki otorite tek bir sabit sayı değildir.

Yeni sıralama şu sinyalleri kullanmalı:

```
jurisdiction match
court level
court chamber
decision date
finality
publication status
legal issue similarity
authority validity
cited/overruled status
source authenticity
event-date compatibility
firm validation
```

Ayrıca “yüksek mahkeme kararı her durumda daha relevant” varsayımı yapılmamalı.

## 2.6 Provenance filtresi düzeltilmeli

V4 retrieval ilk assertion adaylarını:

- dataset,
- jurisdiction,
- `valid_at`

ile filtreliyor.

Ancak son entity provenance listesi çıkarılırken aynı tarih ve jurisdiction filtreleri yeniden uygulanmıyor. Bu nedenle sonuç entity’sine bağlı fakat sorgu tarihiyle ilgisiz assertion’lar cevap içinde görülebilir.

Legal retrieval’da aynı filtrelerin:

```
candidate generation
ranking
provenance hydration
answer citation
```

aşamalarının tamamında korunması gerekir.

## 2.7 Legal audit statik listeye dayanmamalı

`legal_audit.py` önemli bir başlangıç ancak üretimde statik geçerli madde listesi yeterli değildir.

Yeni sistem:

```
Official legal source snapshot
      ↓
Versioned authority registry
      ↓
Citation validation
      ↓
Graph assertion validation
```

kullanmalı.

“TBK Madde 49 var mı?” kontrolünden öte:

- ilgili tarihte var mıydı?
- madde numarası değişmiş miydi?
- mülga mıydı?
- geçici madde mi?
- alıntı gerçekten o maddeye mi ait?
- kaynak hangi snapshot’tan geliyor?

kontrol edilmeli.

## 2.8 Synthetic benchmark üretim için yeterli değil

Mevcut legal generator:

- beş kanun,
- birkaç Yargıtay dairesi,
- sentetik karar metinleri

üzerinden çalışıyor.

Bu, retrieval regression testi için yararlı olabilir ancak hukuki güvenilirliği ölçemez.

Gerçek değerlendirme seti:

- anonimleştirilmiş gerçek dosya belgeleri,
- gerçek mevzuat sürümleri,
- gerçek karar metadata’ları,
- avukat tarafından hazırlanmış ground truth,
- yanlış atıf tuzakları,
- tarihsel mevzuat tuzakları,
- çelişkili belge senaryoları

içermeli.

---

# 3. Rakip uygulamalardan çıkarılacak ürün dersleri

## Harvey ve Legora: çalışma alanı ve workflow

Harvey; Assistant, Vault, legal research, document analysis, workflow ve agent katmanlarını tek platformda birleştiriyor. Legora ise DMS, hukuk kaynakları, üçüncü taraf servisler ve MCP connector’larını ortak bir agentic çalışma alanına bağladığını; orchestration katmanında tool routing, memory management ve guardrail kullandığını belirtiyor.

**MESA için ders:**

Kullanıcıya yalnızca bir chat ekranı vermek yeterli değil. Dosya, araştırma, belge inceleme ve taslak süreçlerinin aynı matter context’i içinde yaşaması gerekir.

## CoCounsel, Lexis ve vLex: otoriter kaynak

CoCounsel’ın temel avantajı Westlaw ve Practical Law içeriğine dayanması; Lexis+ with Protégé araştırma, drafting ve analiz akışlarını LexisNexis içeriğiyle birleştiriyor. Vincent ise vLex’in geniş global hukuk veri tabanını araştırma, litigation ve transactional workflow’larda kullanıyor.

**MESA için ders:**

MESA’nın yalnızca LLM cevabı vermesi yeterli değildir. Güvenilir hukuk kaynağına erişim veya lisanslı platform entegrasyonu gerekir.

Ancak MESA’nın kendi başına Lexis, vLex veya Lexpera ölçeğinde içerik veri tabanı kurması ilk hedef olmamalı.

## Spellbook ve Luminance: Word ve sözleşme workflow’u

Spellbook Word içinde drafting, redline ve contract review sunuyor. Luminance ise sözleşme üretimi, müzakere, analiz, yükümlülük ve CLM süreçlerine odaklanıyor.

**MESA için ders:**

Sözleşme ürünü yapılacaksa yalnızca web chatbot yeterli değildir. Word entegrasyonu, redline, playbook ve clause library gerekir.

Bu nedenle sözleşme modülü ilk ürün olmamalı; pazar güçlü oyuncularla dolu.

## Clio: sonuç üreten büro otomasyonu

Clio Manage AI, mahkeme belgelerinden deadline çıkarmak, takvim ve görev oluşturmak, billing ve diğer practice-management aksiyonlarını tamamlamak üzere konumlanıyor.

**MESA için ders:**

Kullanıcı “belgeyi özetle” değil:

```
süreyi bul
görevi oluştur
avukata ata
onay al
takvime ekle
```

şeklinde tamamlanmış workflow ister.

Ancak faturalandırma ve tam CRM ilk aşamada MESA’ya eklenmemeli.

## Türkiye’deki sistemler

Lexpera; mevzuat, içtihat ve literatür araştırmasına, Kazancı ise geniş yargı kararı ve mevzuat veri tabanına odaklanıyor. Sinerji mevzuat/içtihatla birlikte dava ve icra takibi sunuyor. UYAP ise dava dosyası inceleme, evrak gönderme, dava/icra başlatma ve elektronik ödeme gibi resmî işlemleri gerçekleştiriyor.

**MESA için ders:**

MESA:

- Lexpera/Kazancı yerine içerik yayıncısı,
- Sinerji yerine tam dava takip sistemi,
- UYAP yerine resmî işlem platformu

olmaya çalışmamalı.

Bunları bir matter intelligence katmanı üzerinden bağlamalı.

---

# 4. Yeni ürün konumlandırması ve kesin ürün kararları

## Eski yaklaşım

```text
Hukuk chatbotu
+ belge yükleme
+ mevzuat arama
+ dilekçe üretme
```

Bu yaklaşım çok genel, kolay kopyalanabilir ve MESA’nın provenance, memory, mutation ve graph gücünü yeterince kullanmaz.

## Revize yaklaşım

> **MESA Law, bireysel avukatlar ve küçük hukuk büroları için her dava dosyasına özel, kaynaklanabilir, zaman duyarlı ve insan denetimli bir matter intelligence platformudur.**

Ana ürün mesajı:

```text
Dosyanızı anlayın.
Her iddianın kaynağını görün.
Çelişkileri tespit edin.
Doğru tarihteki hukuku bulun.
Kaynaklı taslak üretin.
Süreleri görün ve doğrulayın.
Nihai kararı siz verin.
```

## İlk hedef kullanıcı

Kesin hedef kitle:

```text
Bireysel avukatlar
+
3–20 kişilik küçük hukuk büroları
```

İlk ürün; büyük kurumsal hukuk departmanları veya yüzlerce kullanıcılı bürolar için optimize edilmeyecek. Buna göre öncelikler:

- sade kurulum ve onboarding,
- güçlü fakat anlaşılır matter yetkilendirmesi,
- düşük operasyon maliyeti,
- tek büroya özel deployment,
- belge merkezli kullanıcı deneyimi,
- avukatın mevcut çalışma alışkanlıklarını bozmayan iş akışlarıdır.

## İlk hukuk alanı

İlk sürüm belirli bir hukuk dalına kilitlenmeyecek.

> **MVP, genel dava dosyası analizine odaklanacak; hukuk dallarına özel derin modüller daha sonra eklenecektir.**

Ortak domain:

```text
Taraflar
Belgeler
Olaylar
İddialar
Savunmalar
Deliller
Hukuki meseleler
Mevzuat ve içtihat
Süreler
Taslaklar
İnsan onayı
```

İş hukuku, ticaret hukuku, aile hukuku, icra ve diğer alanlar sonradan ontology, extraction, deadline rule ve playbook eklentileriyle derinleştirilecektir.

## Desteklenen hukuk kapsamı matrisi

“Genel dava analizi” ifadesi bütün hukuk dallarında uzman sonuç üretileceği anlamına gelmeyecektir. İlk sürümün ürün sözleşmesi şöyledir:

```text
Ülke: Türkiye
Ana dil: Türkçe
Saat dilimi: Europe/Istanbul
Temel kapsam: Ortak dava dosyası zekâsı

Desteklenen ortak işlemler:
- belge kabulü ve sınıflandırma,
- taraf, tarih, olay, iddia, savunma ve delil çıkarımı,
- kronoloji,
- kaynaklı matter Q&A,
- güncel/tarihsel mevzuat ve yüksek mahkeme kararı araması,
- sınırlı kaynaklı taslak,
- olası süre ve görev tespiti.

Rule pack tamamlanmadan uzman sonuç üretilmeyecek alanlar:
- ceza yaptırımı ve ceza tayini,
- icra hesapları,
- faiz, harç ve tazminat hesabı,
- zamanaşımı/kesin hak düşürücü süre sonucu,
- kanun yolu süresinin kesinleştirilmesi,
- aile hukukuna özel sonuçlar,
- idari yargıya özgü usul sonuçları.
```

Destek seviyesi UI ve API’de açıkça gösterilecektir:

```text
GENERAL_SUPPORTED
RULE_PACK_SUPPORTED
EXPERIMENTAL
DOCUMENT_ANALYSIS_ONLY
NOT_SUPPORTED
```

Rule pack bulunmayan alanda sistem belge içeriğini analiz edebilir; ancak uzman hukuki sonuç veya kesin süre üretemez. Bu sınır, cevap metninde ve dışa aktarılan raporda görünür olmalıdır.

## MVP stratejisi: geniş fakat sınırlı

Sistem hazırlanırken MESA hukuk verileriyle önceden doldurulacaktır. MVP tek bir özellikten oluşmayacaktır.

MVP’de sınırlı kapsamla birlikte bulunacak dört ana iş akışı:

```text
1. Dosya yükleme ve matter analizi
2. Mevzuat/içtihat araştırması
3. Kaynaklı taslak üretimi
4. Tebligat ve belgelerden süre/görev çıkarımı
```

Buradaki karar:

```text
Özellik genişliği: Dört ana modülün tamamı
Özellik derinliği: Güvenilir temel senaryolar
```

Örneğin taslak modülü tüm dilekçeyi otonom biçimde üretmeyecek; doğrulanmış matter olguları ve seçilmiş kaynaklar üzerinden kontrollü bölüm taslakları oluşturacaktır.

## İlk pilot ve başarı ölçümü

İlk pilot:

```text
2–3 küçük hukuk bürosu
+
kontrollü matter seti
```

ile yürütülecektir.

North-star metriği:

> **Bir avukatın yeni bir dava dosyasını anlamak ve ilk çalışma notunu hazırlamak için harcadığı süreyi, kaynak doğruluğunu ve insan kontrolünü bozmadan ne kadar azaltıyoruz?**

Pilot başarısı yalnız kullanım sayısıyla değil; kaynak doğruluğu, avukat kabul oranı, kritik düzeltme oranı ve dosya hazırlama süresindeki azalma ile ölçülecektir.

---

# 5. Nihai sistem mimarisi ve kesin platform sınırları

Bu revizyonun temel kararı şudur:

> **MESA-Law önce kendi canonical hukuk ürünü olarak kurulacak; MESA intelligence katmanı ürünün yaklaşık %35–45’i tamamlandıktan sonra, önceden tanımlanmış bir port üzerinden bağlanacaktır.**

MESA ilk geliştirme adımı değildir; ancak literal anlamda son gün eklenecek bir eklenti de değildir. Matter, yetki, belge, OCR, provenance, review ve temel frontend çalışmadan MESA entegrasyonuna geçilmez. Gerçek araştırma, semantic retrieval, assertion graph ve MESA-backed Q&A ise pilot öncesinde tamamlanır.

```text
Aşama A — MESA’sız ürün çekirdeği
Canonical data + security + documents + review + mock intelligence

Aşama B — Geç MESA entegrasyonu
Contract gap analysis + minimal generic MESA changes + real adapter + rebuild
```

## 5.1 Repo ve çalışma zamanı ayrımı

```text
Yasou13/MESA
├── sektör bağımsız memory/retrieval/provenance çekirdeği
├── V4 API ve capability endpoint’i
├── MESA MCP — yalnız geliştirme ajanları
└── bağımsız release döngüsü

Yasou13/MESA-Law
├── canonical hukuk backend’i
├── frontend
├── worker ve belge pipeline’ı
├── hukuk domain’i
├── intelligence port + mock adapter
├── daha sonra gerçek MESA V4 adapter
└── bağımsız ticari release döngüsü
```

Kesin bağımlılık yönü:

```text
MESA-Law domain/application
        ↓
MesaIntelligencePort
        ├── MockMesaAdapter             — başlangıç ve test
        ├── PostgresLexicalAdapter      — degraded/basic fallback
        └── MesaV4HttpAdapter           — entegrasyon fazından sonra
```

MESA-Law domain katmanı:

- `mesa_client` import etmez,
- MESA tablolarına SQL atmaz,
- MESA MCP kullanmaz,
- MESA hata tiplerini dışarı sızdırmaz,
- adapter dışında MESA endpoint adlarını bilmez.

MCP’nin rolü değişmez:

```text
Claude Code / Codex / Antigravity
        ↓
MESA MCP Gateway
        ↓
MESA geliştirme ve kontrol yüzeyi
```

MESA MCP ürün runtime protokolü değildir.

## 5.2 İki evreli çalışma mimarisi

### Evre A — MESA bağlanmadan çalışan ürün

```text
Kullanıcı
   ↓
Next.js Web
   ↓ REST + SSE
FastAPI
   ├── PostgreSQL canonical domain
   ├── PostgreSQL FTS metadata/document fallback
   ├── S3/MinIO immutable documents
   ├── Durable PostgreSQL jobs/outbox
   ├── OCR/parser/deterministic extraction
   ├── Review/approval/audit
   └── MockMesaAdapter
```

Bu evrede şu ekran ve akışlar gerçek verilerle çalışır:

- kullanıcı, firma ve matter,
- matter üyeliği ve ethical wall,
- belge yükleme, karantina ve chain of custody,
- OCR/parsing ve source locator,
- belge görüntüleme,
- review queue,
- taslak revision altyapısı,
- bildirim ve audit,
- metadata ve PostgreSQL full-text arama.

Timeline, claims/evidence ve Q&A ekranları ilk olarak deterministik fixture veya `MockMesaAdapter` ile geliştirilir. Mock yalnız mutlu senaryoyu değil gecikme, hata ve eksik kaynak durumlarını da üretir.

### Evre B — Gerçek MESA intelligence

```text
FastAPI application services
        ↓
MesaIntelligencePort
        ↓
MesaV4HttpAdapter
        ↓
MESA V4 API
        ↓
MESA SQL + LanceDB + Kùzu
```

Bu evrede eklenenler:

- MESA document/revision/chunk projection,
- typed legal assertion projection,
- vector + lexical + graph retrieval,
- temporal hukuk kaynağı retrieval,
- real timeline/claim/evidence synthesis,
- matter Q&A,
- rebuild/replay,
- MESA capability ve contract testleri.

## 5.3 Kesin teknoloji yığını

### Frontend

```text
Next.js App Router
React + TypeScript
pnpm workspace
Tailwind CSS
shadcn/ui
TanStack Query
React Hook Form + Zod
PDF.js
Tiptap
Cytoscape.js — yalnız graph/evidence ekranı gerektiğinde
Vitest + React Testing Library + Playwright
```

Kararlar:

- Next.js içinde hukuk business logic’i yazılmaz.
- Server state TanStack Query ile yönetilir.
- Zustand yalnız PDF zoom, seçili annotation ve panel durumu gibi geçici UI state için kullanılabilir.
- API tipleri FastAPI OpenAPI’dan **Orval** ile üretilir; generated dosyalar elle değiştirilmez.
- Gerçek zamanlı ortak editör MVP dışıdır.

### Backend

```text
Python + uv workspace
FastAPI
Pydantic v2
SQLAlchemy 2 async
Alembic
PostgreSQL + asyncpg
httpx
structlog
OpenTelemetry
pytest + pytest-asyncio + testcontainers
Ruff + mypy
```

İlk mimari **modüler monolit + ayrı worker process** olacaktır. Microservice ayrımı yalnız ölçülmüş ölçek veya güvenlik ihtiyacıyla ADR üzerinden yapılabilir.

### Belge işleme

```text
PyMuPDF             = born-digital PDF text/layout
pikepdf             = PDF doğrulama/sanitization yardımcıları
OCRmyPDF + Tesseract tur = taranmış PDF ve görsel OCR
python-docx          = DOCX
openpyxl             = XLSX
email stdlib         = EML
extract-msg adapter  = MSG
ClamAV               = malware scan
```

Tüm kütüphaneler parser interface arkasında kalır. Parser implementation ve sürümü canonical pipeline kaydına yazılır.

### Infrastructure

```text
PostgreSQL           = canonical veri + jobs/outbox + FTS fallback
S3/MinIO             = immutable original/derived artifacts
Redis                = cache/rate limit/SSE fan-out; source of truth değil
Keycloak             = geliştirme/pilot OIDC + TOTP MFA
Caddy                 = same-origin reverse proxy ve TLS
Docker Compose        = development/pilot
OpenTelemetry Collector
Prometheus + Grafana
Loki + Tempo
```

## 5.4 Veri sahipliği ve canonical artifact sözleşmesi

```text
PostgreSQL
= domain ve operasyon kayıtları

S3 / MinIO
= original ve immutable derived artifacts

MESA
= tamamen yeniden üretilebilir intelligence projection
```

Canonical parsed artifact:

```text
original.ext
parsed/document.jsonl
parsed/pages/{page}.json
ocr/searchable.pdf
ocr/text.jsonl
thumbnails/{page}.webp
exports/...
```

PostgreSQL şunları indeksler:

- revision ve artifact URI/hash,
- page/section/source locator,
- parser/OCR sürümü,
- pipeline run ve durum,
- FTS için normalize edilmiş güvenli metin,
- chain-of-custody olayları.

MESA içeriği silindiğinde PostgreSQL + object storage üzerinden rebuild yapılabilir.

## 5.5 Mantıksal kod ve veri kararları

### Kimlik standardı

- Bütün public/domain ID’ler uygulama tarafından üretilen **UUIDv7** olacaktır.
- Haricî sistem ID’leri ayrı `external_reference` alanında tutulur.
- Tenantlar arasında anlam taşıyan sequential ID kullanılmaz.
- Source segment kimliği parsing run’a bağlı immutable ID’dir; reprocess yeni parsing revision oluşturur.

### Zaman standardı

- Veritabanında bütün timestamp’ler UTC ve timezone-aware tutulur.
- UI `Europe/Istanbul` ve `tr-TR` ile gösterir.
- Hukuki olay tarihi, belge tarihi, observed time ve system time ayrı alanlardır.

### Transaction sınırı

- Bir application command en fazla bir PostgreSQL transaction’ı sahiplenir.
- Network, model, OCR, object storage veya MESA çağrısı açık DB transaction içinde yapılmaz.
- DB commit sonrası dış iş `legal_outbox` ile worker’a teslim edilir.
- “DB yazıldı ama job kayboldu” durumu outbox ile engellenir.

### Idempotency

- Bütün command endpoint’leri `Idempotency-Key` kabul eder.
- Key + tenant + principal + endpoint + request hash saklanır.
- Aynı key farklı payload ile kullanılırsa `409 IDEMPOTENCY_CONFLICT` döner.
- Upload complete, export, approval, purge ve MESA ingestion idempotent olmalıdır.

### Concurrency

- Değiştirilebilir canonical kayıtlarda `version` alanı ve optimistic locking kullanılır.
- API `ETag` / `If-Match` destekler.
- Draft Studio MVP’de tek aktif editor lease + revision lock kullanır.
- Deadline/approval/purge işlemlerinde stale version ile işlem yapılamaz.

### Job lease algoritması

`legal_jobs` PostgreSQL tablosu kullanılacaktır:

```text
PENDING → LEASED → RUNNING → SUCCEEDED
                       └──→ RETRY_WAIT
                       └──→ DEAD_LETTER
```

Lease:

- `FOR UPDATE SKIP LOCKED`,
- `lease_owner`, `lease_expires_at`, heartbeat,
- exponential backoff + jitter,
- maksimum attempt,
- idempotency key,
- dead-letter reason.

İlk sürümde Celery/RQ/Redis queue kullanılmayacaktır.

### Auth ve session

- Keycloak OIDC Authorization Code + PKCE kullanılacaktır.
- FastAPI auth callback ve server-side session’ı yönetir.
- Browser’a `HttpOnly`, `Secure`, `SameSite=Lax/Strict` session cookie verilir.
- Next.js token saklamaz; same-origin `/legal-api` çağrısı yapar.
- State-changing isteklerde CSRF token zorunludur.
- Token veya session localStorage’a yazılmaz.

### API hata formatı

Bütün hatalar `application/problem+json` formatındadır:

```json
{
  "type": "https://errors.mesa.law/source-set-incomplete",
  "title": "Kaynak seti tamamlanmadı",
  "status": 409,
  "code": "SOURCE_SET_INCOMPLETE",
  "detail": "Belgenin bazı sayfaları henüz işlenmedi.",
  "trace_id": "...",
  "retryable": true,
  "details": {}
}
```

Adapter hataları domain error taxonomy’sine çevrilir.

### Feature flag ve config önceliği

```text
Kod güvenli varsayılanı
< deployment config
< tenant config
< matter policy
```

Ancak güvenlik minimumları tenant/matter tarafından gevşetilemez. Config değişiklikleri sürümlenir ve audit edilir. Feature flag’ler DB tabanlı ve tenant-scoped olur; üretim davranışı yalnız environment variable yığınına bırakılmaz.

## 5.6 API ve canlı işlem sözleşmesi

```text
REST                 = ana uygulama API’si
OpenAPI              = Orval generated TypeScript client
SSE                  = OCR/ingestion/research/export progress
WebSocket/Yjs        = MVP sonrası collaboration
202 + operation_id   = uzun işlemler
Idempotency-Key      = command endpoint’leri
ETag / If-Match      = optimistic concurrency
trace_id             = request/job/MESA zinciri
```

Pagination cursor-based olur. Liste endpoint’leri tenant/matter scope’u parametreyle değil authorization context ile uygular.

---

# 6. MESA V4 ile hukuk domain’inin eşleştirilmesi

## Mevcut MESA nesneleri yeniden kullanılmalı

|MESA V4|MESA Law karşılığı|
|---|---|
|Tenant|Hukuk bürosu veya şirket|
|Workspace|Uygulama alanı/practice group|
|Dataset|Matter, firma bilgi bankası veya hukuk kaynağı|
|Document|Evrak, karar, mevzuat veya sözleşme|
|Revision|Belge/mevzuat sürümü|
|SourceChunk|Sayfa, paragraf, madde veya bölüm|
|Entity|Kişi, şirket, mahkeme, kanun, iddia|
|Assertion|Olgu, iddia, hukuki kural veya ilişki|
|Session|Kullanıcı/agent çalışma oturumu|
|Mutation|Yeni veri veya düzeltme işlemi|
|Pipeline run|Belge işleme süreci|

## Dataset türleri eklenmeli

```
MATTER_PRIVATE
FIRM_KNOWLEDGE
PUBLIC_LEGAL_SOURCE
LICENSED_LEGAL_SOURCE
TEMPLATE_LIBRARY
SANDBOX
```

Bir matter sorgusunda izin verilen kapsam:

```
Matter dataset
+
Yetkili firma bilgi dataset’i
+
Yetkili kamu/lisanslı hukuk dataset’i
```

olmalıdır.

Başka matter dataset’i kesinlikle otomatik olarak eklenmemelidir.

---

# 7. Eklenmesi gereken hukuk domain tabloları

Bu tablolar **MESA-Law PostgreSQL şemasında canonical uygulama verisi** olarak tutulmalıdır. MESA’nın generic çekirdek tablolarına hukuk kolonları eklenmemeli ve MESA-Law business logic’i MESA storage şemasına bağlanmamalıdır.

MESA ile ilişki, açık kimlik ve operation mapping tabloları üzerinden kurulmalıdır:

```text
legal_mesa_bindings
legal_mesa_operations
legal_projection_status
```

Örnek mapping alanları:

```text
matter_id
document_id
document_revision_id
mesa_tenant_id
mesa_workspace_id
mesa_dataset_id
mesa_document_id
mesa_revision_id
mesa_mutation_id
mesa_pipeline_run_id
last_projection_status
```

Bu sayede PostgreSQL’deki canonical matter/document kaydı ile MESA’daki türetilmiş intelligence yeniden işlenebilir, replay edilebilir ve bağımsız olarak denetlenebilir.

## Matter

```
legal_matters
matter_members
matter_roles
matter_parties
matter_opponents
matter_external_refs
matter_tags
matter_status_history
```

Önemli alanlar:

```
matter_id
tenant_id
dataset_id
matter_type
jurisdiction
court
docket_number
client_id
responsible_attorney
confidentiality_level
status
opened_at
closed_at
```

## Belge

```
legal_documents
legal_document_pages
legal_document_sections
legal_document_classifications
legal_document_signatures
legal_document_attachments
```

Mevcut `documents` tablosuna domain bilgisi doğrudan doldurulmamalı; `legal_documents.document_id` ile bağ kurulmalı.

## Hukuki kaynak

```
legal_authorities
legal_authority_versions
legal_articles
court_decisions
decision_parties
decision_citations
authority_relationships
source_snapshots
source_connectors
```

## Dosya zekâsı

```
legal_facts
legal_claims
legal_arguments
legal_evidence
legal_evidence_links
legal_events
legal_deadlines
legal_obligations
legal_risks
legal_issues
```

## İnceleme

```
legal_review_items
legal_assertion_reviews
legal_verification_events
legal_approval_requests
legal_quality_findings
```

## Taslak

```
legal_drafts
legal_draft_revisions
legal_draft_sections
legal_draft_claims
legal_draft_citations
legal_clauses
legal_playbooks
```

---

# 8. Legal assertion modeli

Generic assertion tablosu korunmalı ancak hukuk sidecar’ı eklenmeli:

```
legal_assertion_metadata
```

Alanlar:

```
assertion_id
assertion_type
epistemic_status
speaker_entity_id
issue_id
event_id
legal_effect
support_type
review_state
risk_level
reviewed_by
reviewed_at
```

## Assertion türleri

```
SOURCE_FACT
ALLEGATION
ADMISSION
DENIAL
DISPUTED_FACT
VERIFIED_FACT
LEGAL_RULE
PRECEDENT_PRINCIPLE
ARGUMENT
COUNTERARGUMENT
EVIDENCE_CONNECTION
DEADLINE_TRIGGER
OBLIGATION
RISK
STRATEGY
```

## Epistemic durum

```
AI_EXTRACTED
RULE_VALIDATED
MODEL_VALIDATED
REVIEW_REQUIRED
HUMAN_VERIFIED
DISPUTED
REJECTED
SUPERSEDED
```

LLM sonucu hiçbir zaman doğrudan:

```
HUMAN_VERIFIED
```

olamaz.

---

# 9. Belge ingestion mimarisi

## Aşama 1 — Admission

```text
Frontend upload intent ister
 ↓
Backend matter erişimini doğrular
 ↓
Presigned S3/MinIO URL üretir
 ↓
Frontend dosyayı doğrudan object storage’a yükler
 ↓
Backend upload completion doğrulaması yapar
 ↓
MIME + malware + SHA-256 kontrolü
 ↓
PostgreSQL’de canonical document/revision kaydı
 ↓
Durable ingestion job
 ↓
MESA document/revision kaydı ve projection
```

Orijinal dosya PostgreSQL, MESA SQLite veya vector store içine gömülmemelidir. Immutable object key kullanılmalı ve aynı revision dosyasının üzerine yazılmamalıdır.

```text
tenant/{tenant_id}/matter/{matter_id}/document/{document_id}/revision/{revision_id}/original.pdf
```

## Aşama 2 — Parsing

Desteklenecek formatlar:

- PDF,
- taranmış PDF,
- DOCX,
- XLSX,
- TXT,
- EML,
- MSG,
- resim,
- ZIP evrak paketi.

Çıkarılacak bilgiler:

```
page number
paragraph
heading
table
footnote
signature
stamp
attachment
bounding box
OCR confidence
```

## Aşama 3 — Document classification

Örnek türler:

```
DAVA_DILEKCESI
CEVAP_DILEKCESI
BILIRKISI_RAPORU
DURUSMA_TUTANAGI
MAHKEME_KARARI
YARGITAY_KARARI
IHTARNAME
SOZLESME
FATURA
BORDRO
TANIK_IFADESI
TEBLIGAT
```

## Aşama 4 — Deterministik extraction

LLM’den önce:

- dosya numarası,
- tarih,
- tebliğ tarihi,
- T.C. kimlik numarası,
- vergi numarası,
- mahkeme adı,
- esas/karar numarası,
- mevzuat atfı,
- para tutarı,
- imza,
- taraf isimleri

kurallı sistemle çıkarılmalı.

## Aşama 5 — Model extraction

Model:

- olay,
- iddia,
- savunma,
- talep,
- hukuki gerekçe,
- delil bağlantısı,
- çelişki

çıkarır.

## Aşama 6 — Validation

```
Schema validation
Citation validation
Date validation
Entity resolution
Duplicate detection
Contradiction detection
Source-span validation
```

## Aşama 7 — Human review

Yüksek riskli kayıtlar avukat inceleme kuyruğuna gider.

---

# 10. Sayfa ve paragraf provenance

Mevcut `source_ref` ve `evidence_span` iyi bir temel ama yeterli değil.

Yeni source locator:

```
{
  "document_id": "doc_123",
  "revision_id": "rev_2",
  "page": 14,
  "paragraph": 3,
  "section": "Hukuki Nedenler",
  "start_offset": 1240,
  "end_offset": 1378,
  "bounding_box": [72, 104, 520, 183],
  "text_hash": "sha256:...",
  "ocr_confidence": 0.97
}
```

Kullanıcı kaynak linkine bastığında belge görüntüleyici doğrudan ilgili sayfa ve paragrafı vurgulamalı.

---

# 11. Tarihsel mevzuat sistemi

Her hukuk kaynağı için şu tarihler ayrılmalı:

```
published_at
effective_from
effective_to
repealed_at
decision_date
finalized_at
accessed_at
observed_at
```

`valid_from` ve `valid_to` tek başına bütün hukuk kaynaklarını temsil edemez.

## Mevzuat grafiği

```
Kanun
 └── Madde
      ├── Version 1
      ├── Version 2
      └── Version 3
```

İlişkiler:

```
AMENDS
REPEALS
REPLACES
INTERPRETS
CITES
SUPERSEDES
IMPLEMENTED_BY
```

Sorgu:

```
“3 Mart 2021 tarihinde uygulanacak hüküm nedir?”
```

geldiğinde sistem olay tarihine göre ilgili sürümü seçmeli.

---

# 12. Hukuki veri ve kaynak stratejisi

MESA başlangıçta yalnız boş bir retrieval motoru olarak bırakılmayacaktır. Ürün geliştirilirken kontrollü hukuk veri katmanları oluşturulacak ve MESA bu verilerle doldurulacaktır.

## Kaynak sınıfları

```text
OFFICIAL
LICENSED
FIRM_INTERNAL
MATTER_PRIVATE
USER_PROVIDED
ANONYMIZED_EXAMPLE
OPEN_WEB
```

`OPEN_WEB` hiçbir zaman resmî veya lisanslı kaynağa eşdeğer otorite kabul edilmeyecektir.

## Başlangıç veri kapsamı

Kesin başlangıç kapsamı:

```text
1. Güncel mevzuat
2. Tarihsel mevzuat sürümleri
3. Yargıtay kararları
4. Danıştay kararları
5. Anayasa Mahkemesi kararları
6. Elle yüklenen ve doğrulanan diğer kararlar
7. Anonimleştirilmiş örnek dava belgeleri
8. Bu belgelerden üretilmiş doğrulanmış timeline, iddia ve delil kayıtları
```

Akademik eserler, kitaplar, makaleler ve geniş dilekçe/şablon arşivleri ilk aşamada kapsam dışı kalacaktır. Bunlar telif, lisans ve kalite politikası netleştirildikten sonra ayrı kaynak sınıfları olarak eklenebilir.

## Kaynak edinme aşamaları

### Geliştirme aşaması

- resmî ve açık kamu kaynakları,
- elle yüklenen ve doğrulanan kararlar,
- anonimleştirilmiş örnek dava dosyaları,
- sentetik veriler yalnız regression ve saldırı testleri için.

### Ticari aşama

- lisanslı hukuk veri tabanları,
- müşterinin kendi karar ve bilgi arşivi,
- hukuk bürosunun anonimleştirilmiş ve onaylanmış içerikleri,
- izinli DMS ve kaynak connector’ları.

Ticari veri tabanlarına scraping yoluyla bağlanılmayacaktır. Entegrasyon yalnız açık API, sözleşme veya lisans kapsamında yapılacaktır.

## Kaynak lisans metadata’sı

Her connector veya kaynak paketi için:

```text
license_scope
allowed_usage
embedding_allowed
caching_allowed
quotation_limit
retention_rule
source_owner
contract_reference
```

alanları tutulacaktır.

Lisans politikası izin vermiyorsa tam metin, embedding veya uzun süreli cache oluşturulmayacaktır.

## Güncellik ve senkronizasyon politikası

Her kaynak snapshot’ı için:

```text
last_successful_sync
snapshot_id
snapshot_hash
source_status
stale_after
observed_at
```

tutulacaktır.

Durumlar:

```text
CURRENT
STALE
SYNC_FAILED
LICENSE_RESTRICTED
SOURCE_UNAVAILABLE
```

Kaynak `STALE` veya `SYNC_FAILED` olduğunda:

- kullanıcıya açık uyarı gösterilir,
- kullanılan snapshot belirtilir,
- kritik araştırma çıktısının finalleştirilmesi engellenebilir,
- sistem sessizce güncelmiş gibi kesin sonuç üretmez.

## Legal content operations

Hukuk verisi senkronizasyonu yalnız teknik connector işi değildir. Aşağıdaki sorumluluklar açıkça atanacaktır:

```text
Source Connector Owner
Legal Content Reviewer
Ontology Maintainer
Snapshot Release Approver
```

Her hukuk veri yayını bağımsız sürümlenir:

```text
TR-LEGAL-YYYY.MM.DD.N
```

Yayın süreci:

```text
Fetch/import
→ integrity ve license kontrolü
→ normalize
→ duplicate/alias çözümü
→ temporal relation üretimi
→ hukukçu örneklem incelemesi
→ benchmark
→ snapshot imzalama
→ canary
→ ACTIVE
```

Kaynak hatası, mülga kayıt, yanlış metadata veya duplicate karar için ayrı issue/review kuyruğu bulunur. Kaynak senkronizasyon SLA’sı ve on-call sahibi tanımlanmadan ticari araştırma özelliği etkinleştirilmez.

## Anonimleştirme kalite sözleşmesi

Başlangıç örnek dosyaları ve izin verilen müşteri verileri aşağıdaki yaşam döngüsünden geçer:

```text
RAW
→ AUTO_REDACTED
→ HUMAN_REVIEWED
→ APPROVED_FOR_BENCHMARK
veya
→ APPROVED_FOR_TRAINING
```

Kontroller:

- ad, soyad, T.C. kimlik ve vergi numarası,
- adres, telefon, e-posta,
- dava/dosya numarası,
- dolaylı kimlik belirleyiciler,
- belge metadata’sı ve dosya adı,
- görsel ve taranmış sayfadaki bilgiler,
- embedded attachment’lar,
- tersine kimliklendirme riski.

Benchmark onayı eğitim onayı değildir. Eğitim için ayrıca açık izin, kullanım amacı, anonimleştirme raporu ve insan onayı gerekir.

---

# 13. Hukuki araştırma motoru

## Query planner

Kullanıcı sorusundan:

```
jurisdiction
practice area
legal issue
event date
authority types
matter scope
requested output
```

çıkarılır.

## Retrieval lanes

```
Matter documents
Firm knowledge
Official/licensed legal sources
Vector search
BM25
Graph traversal
Citation graph
Temporal filtering
```

## Rerank

Yeni sıralama:

```
relevance
× temporal validity
× jurisdiction compatibility
× authority quality
× source authenticity
× citation support
× attorney validation
```

Bu çarpanlar kör matematiksel ağırlıklar olmamalı; candidate sınıfları arasında kontrollü ranking uygulanmalı.

## Research çıktısı

```
Issue
Short answer
Applicable law
Relevant facts
Analysis
Counterarguments
Uncertainties
Missing information
Sources
Review status
```

Her önemli cümle bir veya daha fazla source claim’e bağlı olmalı.

## “Bulunamadı” ile “yoktur” ayrımı

Retrieval sonucu belge bulunmaması, ilgili olgunun veya delilin gerçekte bulunmadığı anlamına gelmez. Sistem üç ayrı durumu koruyacaktır:

```text
EVIDENCE_FOUND
NO_EVIDENCE_RETRIEVED
SOURCE_SET_INCOMPLETE
```

Aşağıdaki koşullardan biri varsa sonuç otomatik olarak `SOURCE_SET_INCOMPLETE` sayılır:

- matter belgelerinin bir kısmı henüz işlenmemişse,
- OCR veya parsing kuyruğu tamamlanmamışsa,
- hukuk kaynağı `STALE` veya `SYNC_FAILED` ise,
- vector/graph/retrieval bileşeni degraded moddaysa,
- kullanıcının yetkisi bazı kaynakları kapsamıyorsa.

Sistem “Dosyada böyle bir delil yoktur” yerine şu tür kapsamlı ifade kullanmalıdır:

> “Yetkili olduğum ve işlenmesi tamamlanan mevcut kaynaklarda bu iddiayı destekleyen bir belge bulunamadı.”

## Confidence ve kaynak desteğinin gösterimi

Modelin ürettiği ham yüzde kullanıcıya hukukî kesinlik gibi gösterilmeyecektir. Confidence, kaynak desteği ve insan inceleme durumu ayrı alanlardır:

```text
Extraction confidence: LOW | MEDIUM | HIGH
Source support: NONE | PARTIAL | STRONG | CONTRADICTED
Source coverage: COMPLETE | INCOMPLETE | UNKNOWN
Human review: PENDING | REVIEWED | APPROVED
```

Yüzdesel skor yalnız benchmark ile kalibre edilmiş ve kullanım amacı belgelenmişse iç kalite ekranında gösterilebilir. Son kullanıcı ekranında tercih edilen gösterim kategorik durum ve açıklamadır.

---

# 14. Citation verification

Taslak veya araştırma cevabı üretilmeden önce:

```
Generated claim
 ↓
Claim segmentation
 ↓
Supporting source lookup
 ↓
Exact quote verification
 ↓
Authority/date validation
 ↓
Citation formatting
 ↓
Unsupported claim rejection
```

Durumlar:

```
SUPPORTED
PARTIALLY_SUPPORTED
CONTRADICTED
OUTDATED_SOURCE
UNVERIFIED
NO_SOURCE
```

`NO_SOURCE` veya `CONTRADICTED` iddialar final metinde otomatik olarak gizlenmeli ya da açık uyarı almalıdır.

---

# 15. Matter intelligence modülleri

## Matter Overview

- taraflar,
- dava bilgisi,
- avukatlar,
- dosya aşaması,
- hukuki meseleler,
- riskler,
- yaklaşan süreler,
- son belge değişiklikleri.

## Chronology

Her olay:

```
date
event type
actors
description
source
verification state
disputed status
```

taşımalı.

## Claims Matrix

```
Davacının iddiası
├── Destekleyen belgeler
├── Çelişen belgeler
├── Davalının cevabı
├── Uygulanabilir hukuk
├── Eksik delil
└── İnceleme durumu
```

## Evidence Map

Deliller:

```
supports
contradicts
authenticates
weakens
irrelevant
requires_review
```

bağlarıyla iddialara bağlanmalı.

## Issue Tree

```
Hukuki mesele
├── Unsur 1
├── Unsur 2
├── Unsur 3
├── Dosya olguları
├── Karşı argüman
└── Eksik bilgi
```

---

# 16. Draft Studio

## İlk sürüm

Web tabanlı editör:

- kaynaklı paragraf,
- citation chip,
- suggestion,
- avukat notu,
- version history,
- approval,
- DOCX export.

## Sonraki sürüm

Word add-in:

- seçili paragrafı kaynakla doğrula,
- citation kontrolü,
- dosyadaki olguları getir,
- clause library,
- playbook kontrolü,
- redline,
- eski/yeni metin karşılaştırma.

Spellbook ve Lexis gibi ürünlerin Word içinde çalışması, avukatın mevcut çalışma alışkanlığından kopmamasının önemli olduğunu gösteriyor.

## Paragraf durumları

```
HUMAN_WRITTEN
AI_DRAFTED
SOURCE_SUPPORTED
SOURCE_MISSING
OUTDATED_AUTHORITY
ATTORNEY_REVIEWED
APPROVED
```

---

# 17. Deadline sistemi

MESA Law süreyi otomatik “kesin” kabul etmemeli.

Akış:

```
Tebligat veya karar belgesi
 ↓
Date extraction
 ↓
Possible deadline rules
 ↓
Calendar calculation
 ↓
Conflict/holiday controls
 ↓
Attorney verification
 ↓
Calendar task
```

Durum:

```
DETECTED
CALCULATED
REVIEW_REQUIRED
VERIFIED
CALENDAR_CREATED
```

Süre hesabı daima:

- kaynak belge,
- tetikleyici olay,
- uygulanan kural,
- hesaplama açıklaması

göstermeli.

## Deadline rule engine yönetişimi

Süre hesapları prompt içine yazılmış serbest kurallarla değil, sürümlü ve kaynaklı rule pack’lerle çalışacaktır.

Her kural en az şu alanları taşımalıdır:

```text
deadline_rule_id
rule_pack_id
jurisdiction
procedure_type
trigger_type
service_method
calculation_method
effective_from
effective_to
holiday_calendar_version
legal_source_id
source_snapshot_id
reviewed_by
approved_at
status
```

Rule pack yaşam döngüsü:

```text
DRAFT
→ LEGAL_REVIEW
→ TESTED
→ APPROVED
→ ACTIVE
→ SUPERSEDED / RETIRED
```

Hesaplama motoru şu konuları açıkça modellemelidir:

- tebliğ yöntemi ve tebliğ tarihi,
- başlangıç gününün hesaba katılması,
- gün/hafta/ay/yıl esaslı süreler,
- hafta sonu ve resmî tatil,
- adli tatil,
- sürenin durması veya uzaması,
- saat dilimi,
- olay tarihinde geçerli kural,
- mahkeme veya kurum özel takvimi.

Aktif ve onaylı rule pack bulunmuyorsa sistem kesin tarih üretmez:

```text
POTENTIAL_DEADLINE
RULE_PACK_MISSING
ATTORNEY_CALCULATION_REQUIRED
```

Her yeni veya değişen rule pack; unit test, tarih sınırı testi, tatil takvimi testi, hukukçu incelemesi ve canary kullanımı tamamlanmadan aktif olamaz.

---

# 18. Model mimarisi ve model yönetişimi

Mevcut “her zaman iki LLM” yaklaşımı yerine görev, risk, veri hassasiyeti ve maliyet bazlı routing kullanılacaktır.

## Görev bazlı routing

### Deterministik

- citation parser,
- tarih ve dosya numarası,
- PII tespiti ve maskeleme,
- para tutarı,
- madde ve karar numarası,
- hash ve signature doğrulaması.

### Küçük yerel encoder

- belge sınıflandırma,
- section segmentation,
- semantic retrieval,
- entity candidate generation,
- duplicate candidate generation.

### Tek generative model

- belge özeti,
- standart entity extraction,
- açık iddia ve talep çıkarımı,
- düşük riskli yapılandırılmış çıktı.

### İkinci model veya doğrulayıcı

- çelişki tespiti,
- hukuki kural sentezi,
- source–claim kontrolü,
- karmaşık timeline,
- yüksek riskli drafting,
- kritik citation doğrulaması.

### İnsan

- doğrulanmış olgu,
- süre,
- strateji,
- müvekkile gönderilecek görüş,
- final dilekçe,
- kalıcı silme,
- legal hold kaldırma,
- firma hafızasına aktarım.

## Matter bazlı model ve veri çıkış profilleri

Her matter aşağıdaki profillerden birini kullanacaktır:

```text
LOCAL_ONLY
REDACTED_CLOUD
APPROVED_CLOUD
NO_GENERATIVE_PROCESSING
```

Varsayılan profil `REDACTED_CLOUD` olacaktır; sistem veri hassasiyetine göre daha sıkı profil önerebilir fakat otomatik olarak daha gevşek profile geçemez.

Her model çağrısında:

```text
provider
model_name
model_version
request_id
sent_data_categories
redaction_status
matter_policy
retention_policy
token_usage
estimated_cost
timestamp
```

audit edilecektir.

## Model yaşam döngüsü

Model statüleri:

```text
CANDIDATE
BENCHMARKED
ANONYMIZED_PILOT
CANARY
APPROVED
BLOCKED
DEPRECATED
```

Yeni model sürümü doğrudan production’a alınmayacaktır.

```text
Hukuk benchmark’ı
→ anonim pilot
→ canary
→ insan kabul ölçümü
→ production
```

Her model değişikliğinde:

- eski modelle kalite karşılaştırması,
- hata sınıfları karşılaştırması,
- maliyet karşılaştırması,
- latency karşılaştırması,
- hızlı rollback planı

zorunlu olacaktır.

## Model maliyeti

Her tenant ve matter için:

```text
token_usage
model_cost
cost_per_page
cost_per_research
cost_per_draft
monthly_budget
```

ölçülecektir.

Politika:

```text
Bütçenin %80’i:
Yönetici uyarısı

Bütçenin %100’ü:
Yönetici onayı olmadan yeni ücretli işlem başlatılmaz
```

Gerekirse yerel veya daha düşük maliyetli güvenli fallback kullanılabilir.

## Müşteri verisinin eğitimde kullanılması

Varsayılan:

```text
customer_data_used_for_training = false
```

Eğitim veya fine-tuning için:

- açık müşteri izni,
- güçlü anonimleştirme,
- insan kontrolü,
- ayrı veri seti,
- geri çekilebilir izin

zorunludur.

Avukat düzeltmeleri benchmark adayı olabilir; ancak açık izin olmadan eğitim verisi değildir.

---

# 19. Hukuki memory, düzeltme ve silme yaşam döngüsü

## Assertion yaşam döngüsü

```text
AI_EXTRACTED
    ↓
RULE_VALIDATED
    ↓
MODEL_VALIDATED
    ↓
REVIEW_REQUIRED
    ↓
HUMAN_VERIFIED
    ↓
ACTIVE
```

Bir avukat AI çıkarımını düzelttiğinde eski kayıt silinmez:

```text
AI assertion
→ HUMAN_CORRECTED revision
→ önceki assertion SUPERSEDED
→ düzeltilmiş assertion ACTIVE
→ benchmark adayı
```

Düzeltme kaydında:

```text
corrected_by
corrected_at
previous_value
new_value
reason
source_reviewed
policy_version
```

tutulur.

## Entity yaşam döngüsü ve kapsamı

Entity’ler varsayılan olarak matter içinde ayrı tutulur.

```text
Matter A entity
≠
Matter B entity
```

Sistem olası eşleşmeleri yalnız öneri olarak gösterir. İnsan tarafından onaylanan eşleşmeler yalnız tenant düzeyinde conflict check amacıyla kullanılabilir.

Firma hafızasına aktarım:

```text
anonimleştirme
+ insan onayı
+ izin kontrolü
```

gerektirir.

## Değişiklik ve geri çekme

```text
ACTIVE
 ↓
SUPERSEDED
```

Hatalı veya güvenilmez bilgi:

```text
ACTIVE
 ↓
REJECTED / RETRACTED
```

## Legal hold ve fiziksel silme

Silme önce soft delete ile başlar. Bekleme süresi sonunda kalıcı silmeye geçilir. Legal hold bulunan kayıtlar silinemez.

```text
SOFT_DELETE
 ↓
WAITING_PERIOD
 ↓
LEGAL_HOLD CHECK
 ↓
APPROVAL
 ↓
PURGE MANIFEST
 ↓
OWNERSHIP CHECK
 ↓
RETRACTION
 ↓
STORE CLEANUP
 ↓
DELETION CERTIFICATE
```

Silme manifesti şu katmanları takip eder:

```text
PostgreSQL
Object storage
MESA SQL
LanceDB
Kùzu
Redis cache
Üretilmiş export dosyaları
Geçici OCR dosyaları
Yedekler
```

Yedekten restore sırasında daha önce silinmiş verilerin yeniden canlanması purge manifest üzerinden engellenir.

---

# 20. Güvenlik, gizlilik ve hukuk operasyonu mimarisi

MESA-Law, meslek sırrı ve kişisel veri işleyen yüksek hassasiyetli bir sistem olarak tasarlanacaktır. Uygulama güvenliği yalnız role dayalı erişimden ibaret olmayacaktır.

## Temel erişim modeli

```text
Tenant role
+
Matter membership
+
Ethical wall
+
Document classification
+
Matter model-egress policy
+
Operation approval policy
```

birlikte değerlendirilir.

PostgreSQL Row-Level Security, application authorization’ın altında ikinci savunma katmanı olacaktır.

## Fiziksel tek-tenant izolasyonu

İlk müşteriler yalnız mantıksal değil fiziksel olarak da ayrılacaktır.

Her müşteri için ayrı:

```text
PostgreSQL database
Object storage bucket/prefix
MESA storage root
Encryption key
Application secrets
Worker namespace
Backup set
```

kullanılacaktır.

## Şifreleme ve anahtar yönetimi

“Her müşteriye ayrı key” kararı merkezi bir KMS/HSM uyumlu anahtar yaşam döngüsüyle uygulanacaktır.

```text
Tenant data-encryption key
Object-storage key context
Database/backup key context
Export key context
Key version
Created/rotated/revoked timestamps
Key access audit
```

Kurallar:

- anahtarlar uygulama `.env` dosyasında düz metin tutulmaz,
- production secret’ları secret manager/KMS üzerinden alınır,
- tenant anahtarları birbirinden ayrılır,
- düzenli rotasyon ve eski sürümle decrypt desteği bulunur,
- backup anahtarları ayrı yetki alanında saklanır,
- key erişimi ve rotasyonu audit edilir,
- müşteri kapanışında key revocation prosedürü uygulanır.

İleri kurumsal paket için customer-managed key seçeneği mimari olarak desteklenebilir; MVP’de platform-managed tenant-specific keys kullanılır.

## Entity ve conflict izolasyonu

Entity’ler matter-local tutulur. Otomatik cross-matter merge yapılmaz. Onaylı eşleşme yalnız conflict index’e minimum bilgiyle yazılır; diğer matter’ın gizli içeriği gösterilmez.

## İnsan onayı ve sorumluluk matrisi

Her firma kendi onay politikasını yapılandırabilir; fakat güvenli asgari kuralların altına inemez.

```text
Düşük riskli olgu düzeltmesi
→ Matter erişimi olan avukat

Deadline doğrulama
→ Sorumlu avukat

Hukuki görüşü finalleştirme
→ Sorumlu avukat veya partner

Müvekkile gönderim
→ Yetkili avukat

Firma hafızasına aktarım
→ Bilgi yöneticisi veya partner

Kalıcı silme
→ Matter owner + yönetici

Legal hold kaldırma
→ Yetkili yönetici, gerektiğinde çift onay
```

Her onay kaydı:

```text
who
when
previous_value
approved_value
reason
sources_reviewed
policy_version
```

içerir.

## Solo firm mode

Bireysel avukatta ikinci yönetici veya partner bulunmayabilir. Bu nedenle güvenlik seviyesi düşürülmeden `SOLO_FIRM_MODE` sağlanacaktır.

İki kişilik onay yerine kritik işlemlerde:

```text
risk özetini görüntüleme
→ açık gerekçe yazma
→ MFA ile yeniden doğrulama
→ bekleme/cooling-off süresi
→ ikinci ve ayrı onay adımı
→ değiştirilemez audit kaydı
```

uygulanır.

Örnek kalıcı silme:

```text
İlk silme talebi
→ 24 saat bekleme
→ legal hold tekrar kontrolü
→ MFA ile yeniden doğrulama
→ son onay
→ purge manifest
```

Firma daha sonra yeni kullanıcı eklerse çift onay politikası yeniden etkinleştirilebilir.

## Belge tabanlı prompt injection

Yüklenen bütün belge metinleri:

```text
UNTRUSTED_CONTENT
```

olarak kabul edilir.

Belge içindeki metin:

- tool çağıramaz,
- sistem talimatını değiştiremez,
- retrieval scope genişletemez,
- başka matter’a erişemez,
- izin yükseltemez,
- export veya silme işlemi başlatamaz,
- model profilini değiştiremez.

Tool çağrıları yalnız güvenilir uygulama workflow katmanı tarafından üretilebilir.

## Güvenli dosya karantinası

Yeni dosya hiçbir parsing, OCR veya model pipeline’ına doğrudan alınmayacaktır.

```text
UPLOADED
→ QUARANTINED
→ MIME_VALIDATION
→ MALWARE_SCAN
→ ARCHIVE_SAFETY_CHECK
→ SAFE
veya
→ BLOCKED / MANUAL_REVIEW
```

Kontrol edilecek riskler:

- yanıltıcı dosya uzantısı ve MIME,
- parola korumalı PDF/ZIP,
- ZIP bomb ve iç içe arşiv,
- makrolu DOCM/XLSM,
- aktif JavaScript içeren PDF,
- bozuk veya aşırı büyük dosya,
- bilinmeyen embedded attachment,
- aşırı görsel boyutu veya kaynak tüketimi.

Orijinal dosya karantinada immutable tutulur. `SAFE` kararı verilmeden türetilmiş OCR/metin üretilemez. Bloke edilen dosyanın nedeni kullanıcıya gösterilir ve manuel güvenlik incelemesi audit edilir.

## Kimlik doğrulama ve support erişimi

Tüm kullanıcılarda MFA zorunludur.

İlk aşama:

```text
E-posta/parola
+ MFA
```

İleri aşama:

```text
OIDC
Microsoft Entra ID
Google Workspace
Keycloak
```

Support erişimi:

```text
Varsayılan: Kapalı
Müşteri onayı: Zorunlu
Süre: Kısıtlı
Yetki: Salt okunur varsayılanı
Audit: Zorunlu
```

## Kullanıcı ve oturum yaşam döngüsü

Aşağıdaki akışlar ürünün güvenlik kapsamına dahildir:

- kullanıcı daveti ve davet süresinin dolması,
- parola sıfırlama,
- MFA cihazı kaybı ve recovery code,
- aktif cihaz/oturum listesi,
- bütün cihazlardan çıkış,
- kullanıcıyı devre dışı bırakma,
- eski çalışanın matter sorumluluğunu devretme,
- support ve break-glass oturumlarının ayrı izlenmesi.

Varsayılan politika:

```text
Normal idle timeout: 30 dakika
Kritik işlem için son doğrulama: En fazla 5 dakika önce
Kullanıcı devre dışı bırakma: Bütün session/token’lar anında iptal
Support session: Süreli ayrı token ve matter-scope
Break-glass: MFA + gerekçe + anlık alarm + sonradan zorunlu inceleme
```

## Güvenlik operasyonu

Zorunlu kontroller:

- dependency ve container scanning,
- SBOM,
- secret rotation,
- MFA,
- break-glass hesapları,
- bağımsız pentest,
- incident response planı,
- düzenli güvenlik tatbikatı,
- olay önem seviyeleri,
- müdahale SLA’ları,
- müşteri onaylı süreli support erişimi,
- immutable audit.

Pilot öncesi bağımsız pentest zorunludur.

Incident hedefleri:

```text
SEV1:
15 dakika içinde karşılama/bildirim
4 saat içinde containment hedefi

SEV2:
1 saat içinde karşılama
1 iş günü içinde çözüm veya geçici önlem
```

## Veri yerleşimi

İlk barındırma ve yedekler varsayılan olarak Türkiye’de tutulacaktır. Başka bölgeye veri çıkışı açık müşteri onayı, sözleşmesel güvence ve audit gerektirir.

## Log ve audit saklama

Varsayılan:

```text
Kritik güvenlik/audit kayıtları: 10 yıl
Operasyon kayıtları: 1 yıl
Debug logları: 30 gün
Geçici worker logları: 7–30 gün
```

Legal hold varsa otomatik silme durur.

Loglara şu veriler yazılmaz:

- tam belge metni,
- tam prompt,
- müvekkil sırrı,
- erişim token’ı,
- parola,
- model sağlayıcı secret’ı.

Bunların yerine kimlik, hash, veri kategorisi, boyut ve correlation ID tutulur.

## Ortam ayrımı

```text
development
staging
production
```

tamamen ayrılır. Production verisi geliştirme ortamına taşınmaz. Gerekirse anonimleştirilmiş, minimum, süreli ve audit edilmiş test paketi kullanılır.

---

# 21. Arayüz yapısı

## Ana menü

```
Dashboard
Matters
Documents
Research
Drafts
Legal Sources
Deadlines
Reviews
Firm Knowledge
Activity
Admin
```

## Matter menüsü

```
Overview
Documents
Timeline
Parties
Claims
Evidence
Issues
Research
Drafts
Deadlines
Tasks
Activity
Permissions
```

## Review Center

Tek bir merkezi review kuyruğu:

```
Extracted facts
Potential contradictions
Deadlines
Citation issues
Draft claims
Entity merges
Source updates
Memory improvements
Purge requests
```

## Legal Control Panel

MESA Control Panel’in hukuk sürümü:

```text
System Health
Ingestion Queue
Source Synchronization
AI Activity
Pending Reviews
Citation Failures
Graph Quality
Model Usage
Data Egress
Cross-Matter Denials
Legal Holds
Retention
```

## Bildirim ve eskalasyon merkezi

Aşağıdaki olaylar yalnız dashboard metriği olarak kalmayacaktır:

- deadline yaklaşması,
- review/approval beklemesi,
- kaynak senkronizasyonunun bozulması,
- ingestion veya OCR hatası,
- model bütçesinin dolması,
- support erişiminin açılması,
- model/data-egress politikasının değişmesi,
- legal hold veya purge talebi,
- kritik belge export’u.

Bildirim durumu:

```text
CREATED
DELIVERED
READ
ACKNOWLEDGED
ESCALATED
RESOLVED
```

MVP kanalları:

```text
Uygulama içi bildirim merkezi
Kritik olaylarda e-posta
Deadline ve security olaylarında acknowledgement
Tanımlı süre içinde cevap yoksa eskalasyon
```

## Kullanılabilirlik, yerelleştirme ve erişilebilirlik

```text
Ana dil: Türkçe
Locale: tr-TR
Saat dilimi: Europe/Istanbul
Para biçimi: Türk lirası
WCAG hedefi: 2.2 AA
MVP odağı: Masaüstü ve responsive web
```

Desteklenen tarayıcılar güncel Chrome, Edge, Firefox ve Safari olacaktır. PDF Viewer ve Draft Studio; klavye kullanımı, ekran okuyucu, yüksek kontrast, zoom ve font ölçekleme açısından test edilecektir. Mobil native uygulama MVP kapsamı dışındadır.

---

# 22. API tasarımı

API; REST, OpenAPI-generated client, `Idempotency-Key`, `trace_id` ve uzun işlemlerde `202 Accepted + operation_id` ilkelerini kullanmalıdır.

## Authentication ve capability

```text
GET  /legal/me
GET  /legal/capabilities
GET  /legal/system/health
```

`/legal/capabilities`, bağlı MESA sürümünü ve gerekli özellikleri göstermelidir:

```json
{
  "mesa_version": "0.7.3",
  "capabilities": [
    "typed_assertions",
    "temporal_sources",
    "source_locators_v2",
    "artifact_ownership"
  ]
}
```

## Matter

```
POST   /legal/matters
GET    /legal/matters
GET    /legal/matters/{id}
PATCH  /legal/matters/{id}
POST   /legal/matters/{id}/members
POST   /legal/matters/{id}/close
```

## Documents

```text
POST   /legal/matters/{id}/documents/upload-intent
POST   /legal/documents/{id}/upload-complete
GET    /legal/documents/{id}
GET    /legal/documents/{id}/pages
GET    /legal/documents/{id}/analysis
POST   /legal/documents/{id}/reprocess
GET    /legal/documents/{id}/download-url
```

Upload endpoint’i binary’yi FastAPI sürecinden geçirmek yerine presigned URL üretmelidir. `upload-complete` hash, size ve object metadata doğrulamasından sonra durable ingestion job oluşturmalıdır.

## Intelligence

```
GET  /legal/matters/{id}/timeline
GET  /legal/matters/{id}/claims
GET  /legal/matters/{id}/evidence
GET  /legal/matters/{id}/issues
POST /legal/matters/{id}/ask
```

## Research

```
POST /legal/research
GET  /legal/research/{research_id}
POST /legal/research/{id}/verify
```

## Reviews

```
GET  /legal/reviews
POST /legal/reviews/{id}/approve
POST /legal/reviews/{id}/reject
POST /legal/reviews/{id}/correct
```

## Drafts

```
POST /legal/drafts
GET  /legal/drafts/{id}
POST /legal/drafts/{id}/generate-section
POST /legal/drafts/{id}/verify-citations
POST /legal/drafts/{id}/export
```

## Deadlines

```
GET  /legal/matters/{id}/deadlines
POST /legal/deadlines/{id}/verify
POST /legal/deadlines/{id}/calendar
```

## Operations ve progress

```text
GET    /legal/operations/{operation_id}
GET    /legal/operations/{operation_id}/events
POST   /legal/operations/{operation_id}/retry
POST   /legal/operations/{operation_id}/cancel
```

`events` endpoint’i OCR, ingestion, MESA mutation, research, citation verification ve export ilerlemesini SSE ile yayınlamalıdır.

## Audit

```text
GET /legal/activity
GET /legal/audit
GET /legal/audit/{event_id}
```

Normal activity ile güvenlik/audit olayları ayrı retention ve erişim politikalarına sahip olmalıdır.

---

# 23. Repo, paket, contract ve agent bağlam yapısı

Hukuk uygulaması MESA reposunun içine eklenmez. MESA-Law ayrı repo ve kendi içinde monorepo olacaktır.

## 23.1 MESA reposu

```text
MESA/
├── mesa_memory/
├── mesa_storage/
├── mesa_api/
├── mesa_client/
├── mesa_mcp/
├── mesa_evals/
├── tests/
├── pyproject.toml
└── CHANGELOG.md
```

MESA core ilk ürün fazlarında değiştirilmez; yalnız baseline tag ve contract snapshot alınır. Daha sonra gerçek adapter gap analizi kanıtladığında generic extension point eklenebilir.

## 23.2 MESA-Law monoreposu

```text
MESA-Law/
├── apps/
│   ├── web/
│   ├── api/
│   │   └── mesa_law/
│   │       ├── shared/
│   │       ├── identity/
│   │       ├── firms/
│   │       ├── matters/
│   │       ├── documents/
│   │       ├── reviews/
│   │       ├── notifications/
│   │       ├── timeline/
│   │       ├── claims/
│   │       ├── evidence/
│   │       ├── legal_sources/
│   │       ├── research/
│   │       ├── deadlines/
│   │       ├── drafts/
│   │       ├── conflicts/
│   │       ├── audit/
│   │       └── intelligence/
│   │           ├── port.py
│   │           ├── contracts.py
│   │           ├── mock_adapter.py
│   │           ├── postgres_lexical_adapter.py
│   │           └── mesa_v4_http_adapter.py
│   └── worker/
│
├── packages/
│   ├── ui/
│   ├── api-client/            # generated
│   ├── eslint-config/
│   └── tsconfig/
│
├── legal_domain/
├── legal_ingestion/
├── legal_connectors/
├── infra/
│   ├── compose/
│   ├── caddy/
│   ├── keycloak/
│   ├── observability/
│   └── deployment/
│
├── contracts/
│   ├── mesa/
│   │   ├── required-capabilities.yaml
│   │   ├── openapi-snapshot.json
│   │   └── contract-cases/
│   └── legal-api/
│
├── data/
│   ├── source-manifests/
│   ├── anonymized-samples/
│   └── benchmark-manifests/
│
├── docs/
│   ├── plans/
│   ├── adr/
│   ├── work-orders/
│   ├── handoffs/
│   ├── baselines/
│   └── runbooks/
│
├── scripts/
├── tests/
├── AGENTS.md
├── CLAUDE.md
├── Makefile
├── pyproject.toml
├── pnpm-workspace.yaml
└── mesa-compatibility.yaml     # MESA integration fazında etkinleşir
```

## 23.3 Backend modül standardı

Domain değeri taşıyan modüller:

```text
module/
├── domain/
│   ├── entities.py
│   ├── value_objects.py
│   ├── events.py
│   └── policies.py
├── application/
│   ├── commands.py
│   ├── queries.py
│   ├── handlers.py
│   └── ports.py
├── infrastructure/
│   ├── models.py
│   ├── repository.py
│   └── adapters.py
├── api/
│   ├── router.py
│   └── schemas.py
└── tests/
```

Kurallar:

- API router repository çağırmaz; application handler çağırır.
- Domain katmanı FastAPI, SQLAlchemy, MESA ve provider SDK import etmez.
- Network ve storage adapter’ları infrastructure’da kalır.
- Basit lookup modüllerinde gereksiz ceremony oluşturulmaz.
- `MemoryDAO` veya MESA storage içine hukuk business logic’i eklenmez.

## 23.4 Intelligence portu ve ilk contract

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Sequence

@dataclass(frozen=True)
class SourceCitation:
    document_revision_id: str
    page: int | None
    source_locator_id: str
    excerpt: str | None

@dataclass(frozen=True)
class IntelligenceOperation:
    operation_id: str
    status: str

class MesaIntelligencePort(Protocol):
    async def ingest_document_revision(
        self,
        *,
        tenant_id: str,
        matter_id: str,
        document_revision_id: str,
        idempotency_key: str,
    ) -> IntelligenceOperation: ...

    async def get_operation(self, operation_id: str) -> IntelligenceOperation: ...

    async def ask_matter(
        self,
        *,
        tenant_id: str,
        matter_id: str,
        question: str,
        valid_at: datetime | None,
    ) -> dict: ...

    async def get_timeline(self, *, tenant_id: str, matter_id: str) -> Sequence[dict]: ...
    async def get_claims(self, *, tenant_id: str, matter_id: str) -> Sequence[dict]: ...
    async def get_evidence_map(self, *, tenant_id: str, matter_id: str) -> dict: ...
    async def rebuild_matter(self, *, tenant_id: str, matter_id: str) -> IntelligenceOperation: ...
    async def health(self) -> dict: ...
```

Contract’ın ilk sürümü küçük tutulur. Yeni metoda ihtiyaç varsa önce work order + contract test + ADR açılır; adapter’a özel convenience metodlar domain servislerine sızdırılmaz.

## 23.5 Adapter sırası

```text
1. MockMesaAdapter
2. PostgresLexicalAdapter
3. MesaV4HttpAdapter
4. Embedded adapter — MVP sonrası, gerçek ihtiyaç varsa
```

`MockMesaAdapter`:

- fixture sonuçları,
- kontrollü latency,
- pending operation,
- unavailable,
- projection delayed,
- no evidence,
- incomplete source set,
- stale legal source

senaryolarını üretir.

`PostgresLexicalAdapter`, MESA yokken ve degraded mode’da belge FTS/metadata araması sağlar; semantic veya graph sonucu taklit etmez.

`MesaV4HttpAdapter` yalnız integration work order’ında eklenir. MESA source package’ı uygulama kurulumunun zorunlu pip dependency’si değildir; production iletişimi HTTP contract üzerinden yapılır.

## 23.6 Agent bağlam dosyaları

`AGENTS.md` kısa ve bağlayıcı kuralları içerir:

- master plan ve ADR yolu,
- komutlar,
- test standardı,
- protected paths,
- secret/veri kuralları,
- MESA geç entegrasyon sınırı,
- work-order zorunluluğu.

`CLAUDE.md` aynı kuralları Claude Code’a uygun kısa formda tekrarlar; farklı mimari karar üretmez.

Canonical agent kuralları `docs/agent/AGENT_RULES.md` içinde tutulabilir; wrapper dosyalar bu kaynağa referans verir. Kuralların kopyalanıp zamanla farklılaşmasına izin verilmez.

---

# 24. Deployment, altyapı ve operasyon modelleri

## 24.1 Geliştirme — Docker Compose ve profiller

İlk geliştirme ortamı MESA olmadan açılabilmelidir:

```text
docker compose --profile core up -d
```

`core` profili:

```text
web
legal-api
legal-worker
postgres
redis
minio
keycloak
clamav
caddy
otel-collector
prometheus
grafana
loki
tempo
```

MESA entegrasyon fazında:

```text
docker compose --profile core --profile mesa up -d
```

`mesa` profili:

```text
mesa-api
mesa-worker
mesa-specific stores
```

Başlangıçta `MESA_ENABLED=false` ve `INTELLIGENCE_ADAPTER=mock` olur. Entegrasyon fazında staging’de `INTELLIGENCE_ADAPTER=mesa_v4_http` etkinleştirilir. Production feature flag ve capability gate olmadan adapter değişmez.

## 24.2 İlk ticari kurulum — Tek müşteriye özel bulut

İlk ürün modeli:

> **Her müşteri için ayrı tek-tenant bulut kurulumu**

Her müşteri için ayrı veritabanı, object storage, MESA storage root, encryption key, secret seti, worker namespace ve backup seti kullanılacaktır.

Bu model; küçük bürolarda daha kolay güvenlik denetimi, hata ayıklama ve müşteri güveni sağlar.

## 24.3 Local Secure

Ürün olgunlaştıktan sonra:

```text
MESA-Law Web/API
PostgreSQL
Şifreli yerel object storage
MESA embedded/local
Yerel model veya NO_GENERATIVE_PROCESSING
```

seçeneği sunulabilir.

## 24.4 Multi-tenant SaaS ve hibrit

İlk aşamada yapılmayacaktır. Ürün olgunlaştığında:

```text
Multi-tenant SaaS
Hibrit cloud/local processing
Enterprise isolated deployment
```

ayrı ürün profilleri olarak geliştirilecektir.

## 24.4.1 Tek-tenant’tan SaaS’a geçiş sözleşmesi

İlk müşteriler fiziksel tek-tenant kurulsa da kod ve veri modeli tenant’a özel fork’lara dönüşmemelidir.

Şimdiden zorunlu ilkeler:

```text
Bütün canonical tablolarda tenant_id
Global olarak çakışmayan dış ID
Tenant-portable object key
Tenant export/import manifest
Tenant migration journal
Storage adapter abstraction
Tenant configuration version
Feature flags
```

Her müşteri aynı uygulama sürümünden ve aynı migration setinden çalışmalıdır. Müşteriye özel ihtiyaçlar kaynak kod fork’u yerine configuration, feature flag veya connector eklentisiyle çözülmelidir.

## 24.5 Durable job ve event modeli

OCR, parsing, MESA ingestion, araştırma, citation doğrulama ve export işlemleri HTTP request içinde tamamlanmayacaktır.

```text
API command
    ↓
PostgreSQL job + outbox
    ↓
Worker lease
    ↓
İşlem
    ↓
MESA mutation / object output
    ↓
Job completion receipt
    ↓
SSE progress event
```

Önerilen tablolar:

```text
legal_jobs
legal_job_attempts
legal_job_leases
legal_dead_letters
legal_outbox
legal_operation_events
```

Redis yalnız hızlandırıcıdır; source of truth veya tek durable queue değildir.

## 24.6 Degraded mode

Sistem kısmi arızalarda tamamen kapanmayacaktır.

|Arıza|Davranış|
|---|---|
|MESA kapalı|Matter ve belgeler açılır; AI/retrieval özellikleri sınırlanır|
|LLM kapalı|Deterministik extraction ve normal dosya erişimi devam eder|
|Vector store kapalı|BM25/lexical fallback|
|Graph kapalı|Graph özellikleri kapalı; kaynaklı arama devam eder|
|OCR kapalı|İş `WAITING_FOR_OCR` durumunda dayanıklı kuyrukta bekler|
|Hukuk kaynağı stale|Uyarı gösterilir; kritik finalizasyon engellenebilir|

Kritik işlemler dayanıklı kuyrukta saklanacak, sistem düzeldiğinde otomatik devam edecek ve hiçbir işlem sessizce kaybolmayacaktır.

## 24.7 Backup ve felaket kurtarma

Pilot ve küçük bürolar için:

```text
PostgreSQL RPO: ≤ 15 dakika
Object storage RPO: ≤ 15 dakika
RTO: ≤ 4 saat
Aylık restore testi: Zorunlu
Şifreli ayrı lokasyon yedeği: Zorunlu
```

Kurumsal müşteriler için daha sıkı RPO/RTO seçenekleri sunulabilir.

MESA’nın vector/graph/assertion store’ları tamamen yeniden üretilebilir kabul edilir. PostgreSQL ve object storage canonical kaynaktır.

## 24.8 Kapasite sınırları

MVP varsayılanları:

```text
Tek dosya: 250 MB
Tek belge: 2.500 sayfa
Matter toplamı: 50.000 sayfa
Kullanıcı başına eşzamanlı upload: 5
```

Büyük işler reddedilmek yerine kontrollü batch işleme alınabilir.

## 24.9 Performans hedefleri

```text
Dashboard/liste P95: ≤ 1,5 saniye
Metadata araması P95: ≤ 3 saniye
Kaynaklı matter Q&A P95: ≤ 20 saniye
Taslak bölüm üretimi P95: ≤ 60 saniye
Upload kabulü P95: ≤ 2 saniye
Belge pipeline başarı oranı: ≥ %99
```

OCR ve büyük belge işlemleri asenkron çalışır; progress SSE ile gösterilir.

## 24.10 Gözlemlenebilirlik

OpenTelemetry tabanlı uçtan uca izleme kullanılacaktır.

```text
trace_id
operation_id
mutation_id
job_id
model_request_id
```

ilişkilendirilir.

İzlenecek:

- API latency,
- database query,
- durable job,
- OCR,
- MESA mutation,
- model çağrısı,
- vector/graph projection,
- source synchronization,
- export,
- retry ve dead-letter.

Belge içeriği ve tam prompt observability sistemine yazılmaz.

---

# 25. UYAP stratejisi

UYAP’ı ilk sürümde otomatik kontrol etmeye çalışmak yanlış olur.

## MVP

- UYAP’tan indirilen belge paketi yükleme,
- klasör import,
- evrak metadata eşleme,
- kullanıcı kontrollü dosya numarası eşleme.

## İleri aşama

- resmî ve izinli servis entegrasyonu,
- kullanıcı kontrollü senkronizasyon,
- e-imza workflow’u,
- gönderim öncesi avukat onayı.

Yapılmaması gereken:

- ekran scraping,
- e-imza credential saklama,
- kullanıcı adına kontrolsüz evrak gönderme,
- resmî olmayan otomasyon.

---

# 26. Geliştirme yol haritası — geç MESA entegrasyonu

## Faz 0 — Governance, baseline ve MESA freeze

- MESA mevcut haliyle test edilir ve baseline tag alınır.
- İlk ürün fazlarında MESA core’a değişiklik yapılmaz.
- MESA OpenAPI/capability snapshot kaydedilir.
- MESA-Law master planı, ADR’ler ve agent kuralları repoya konur.
- Work-order sistemi oluşturulur.

**Çıkış kriteri:** mevcut MESA test/benchmark sonucu kayıtlıdır; agentin MESA’yı değiştirmesi protected-path kuralıyla engellenmiştir.

## Faz 1 — MESA-Law product foundation

- monorepo scaffold,
- web/API/worker,
- PostgreSQL, Alembic ve RLS,
- object storage,
- jobs/outbox,
- auth/MFA,
- tenant, matter, membership ve audit,
- OpenAPI → Orval client,
- error/idempotency/concurrency standardı.

**Çıkış kriteri:** MESA olmadan login → matter oluşturma → yetki kontrolü → canonical veri akışı çalışır.

## Faz 2 — Belge ve canonical provenance foundation

- presigned upload,
- quarantine,
- hash ve immutable revision,
- OCR/parser adapters,
- parsed canonical artifacts,
- page/paragraph/bounding-box source locator,
- document viewer,
- chain of custody,
- PostgreSQL FTS.

**Çıkış kriteri:** dijital ve taranmış örnek belgede kaynağa tıklayınca doğru sayfa/span açılır; MESA gerekmez.

## Faz 3 — Intelligence port, mock ve ürün workflow’ları

- `MesaIntelligencePort`,
- `MockMesaAdapter`,
- `PostgresLexicalAdapter`,
- pending/degraded/incomplete senaryoları,
- Review Center,
- timeline/claims/evidence UI fixture akışı,
- Q&A shell,
- draft revision altyapısı,
- notification center.

**Çıkış kriteri:** frontend bütün ana ekranları gerçek canonical veri ve mock intelligence ile uçtan uca çalıştırır; adapter değişimi domain kodunu etkilemez.

## Faz 4 — Hukuk veri staging ve benchmark foundation

- resmî kaynak manifestleri,
- normalize mevzuat package’ları,
- yüksek mahkeme karar metadata’sı,
- anonimleştirilmiş örnek matter’lar,
- content snapshot sürümleme,
- benchmark gold set ve holdout,
- lisans/izin metadata’sı.

Bu fazda veri önce canonical staging formatında hazırlanır; henüz MESA’ya toplu yüklenmez.

**Çıkış kriteri:** versioned legal source package ve küçük golden dataset MESA’dan bağımsız doğrulanabilir.

## Faz 5 — MESA contract gap analizi

- mevcut MESA V4 API gerçek contract testlerine alınır,
- ihtiyaç duyulan port metotları mevcut endpointlerle eşleştirilir,
- eksik capability listesi kanıtla çıkarılır,
- source locator, temporal filter, idempotency, rebuild ve isolation test edilir.

Sonuç üç sınıftan biri olur:

```text
SUPPORTED
ADAPTER_WORKAROUND_ACCEPTABLE
GENERIC_CORE_CHANGE_REQUIRED
```

**Çıkış kriteri:** MESA core değişikliği gerekiyorsa her eksik için ayrı issue, ADR, contract test ve rollback planı vardır.

## Faz 6 — Minimum MESA generic readiness

Yalnız Faz 5’te kanıtlanan generic eksikler uygulanır:

- SourceLocatorV2,
- typed assertion extension metadata,
- temporal metadata/filter consistency,
- V4 capability endpoint,
- idempotent mutation/rebuild,
- stabil REST contract.

Hukuk ontology’si, TBK/mahkeme isimleri, promptlar ve rule pack’ler MESA core’a girmez.

**Çıkış kriteri:** yeni MESA tag’i ve contract testleri yeşildir; önceki MESA davranışı için regression bulunmaz.

## Faz 7 — Gerçek MESA adapter ve rebuild

- `MesaV4HttpAdapter`,
- capability handshake,
- matter/dataset binding,
- document revision ingestion,
- operation polling,
- rebuild-matter/rebuild-tenant,
- mock/real parity contract tests,
- canary feature flag.

**Çıkış kriteri:** aynı golden fixture mock ve gerçek adapter’da şema uyumlu sonuç üretir; MESA silinip canonical kaynaklardan rebuild edilir.

## Faz 8 — Gerçek legal intelligence

- typed extraction,
- timeline/claim/evidence projection,
- temporal mevzuat retrieval,
- source-grounded Q&A,
- citation verification,
- research memo,
- confidence/completeness statüleri,
- human correction/supersede.

**Çıkış kriteri:** her AI iddiası source locator taşır; cross-matter leakage ve approved fabricated citation sıfırdır.

## Faz 9 — Deadline, Draft Studio ve sınırlı entegre MVP

- onaylı deadline rule-pack çekirdeği,
- POTENTIAL_DEADLINE fallback,
- bildirim/eskalasyon,
- Tiptap single-editor draft,
- source chip ve claim support validation,
- external-use approval,
- DOCX/PDF export.

**Çıkış kriteri:** dört MVP workflow’u gerçek MESA ile ve degraded fallback ile çalışır.

## Faz 10 — Security/release/pilot

- full CI matrix,
- SBOM/license scan,
- pentest,
- restore/rebuild/runbook tatbikatı,
- tek-tenant deployment,
- pilot source snapshot,
- pilot onboarding ve ölçüm.

## Sonraki fazlar

- Word Add-in,
- e-mail/calendar,
- DMS,
- lisanslı connector,
- collaboration,
- multi-tenant SaaS,
- izinli UYAP entegrasyonu.

## Her faz için release gate

```text
Work order acceptance criteria
Unit/integration/security tests
Migration dry-run
No secret or real client data
No protected-path violation
Architecture/ADR compliance
Rollback instructions
Handoff report
```

MESA entegrasyonu sonrası ayrıca:

```text
MESA contract tests
Rebuild test
Temporal retrieval benchmark
Cross-dataset isolation
Capability handshake
```

---

# 27. Benchmark, kalite ve production kapıları

## Retrieval

- matter fact recall,
- citation recall,
- issue retrieval,
- cross-document retrieval,
- temporal authority retrieval.

## Extraction

- party recognition,
- document classification,
- event extraction,
- deadline trigger extraction,
- claim/evidence link accuracy,
- source locator accuracy,
- OCR-derived error rate.

## Generation

- citation precision,
- citation completeness,
- unsupported claim rate,
- outdated-authority rate,
- contradiction awareness,
- human correction severity.

## Güvenlik

- cross-matter leakage,
- tenant leakage,
- prompt injection,
- document classification bypass,
- external model data-egress violation,
- support-access policy violation,
- deleted-data resurrection test.

## İnsan kabulü

- attorney correction rate,
- attorney acceptance rate,
- time-to-review,
- false urgency rate,
- false deadline rate,
- file-understanding time reduction.

## Benchmark veri yönetişimi

Benchmark yalnız skor üreten bir klasör değil, sürümlü ve izin kontrollü bir veri ürünüdür.

```text
benchmark_dataset_version
split: train | dev | hidden_test
practice_area
matter_type
document_types
anonymization_status
annotators
adjudicator
ground_truth_version
allowed_uses
created_at
```

Kurallar:

- train/dev/test birbirinden ayrılır,
- hidden test seti prompt ve model geliştirenlerden erişim olarak ayrılır,
- gold answer hukukçu tarafından hazırlanır,
- iki annotator anlaşmazsa adjudicator karar verir,
- benchmark sonucu model, prompt, ontology ve pipeline sürümüyle saklanır,
- yeni release önceki release ile aynı holdout sette karşılaştırılır,
- müşteri verisi açık izin olmadan benchmark’a alınmaz,
- `APPROVED_FOR_BENCHMARK`, `APPROVED_FOR_TRAINING` anlamına gelmez.

## Kesin üretim engelleri

```text
Cross-matter leakage > 0
Tenant leakage > 0
Unverified final deadline > 0
Fabricated citation in approved output > 0
Source-required approved claim without citation > 0
Final external output without human approval > 0
Unauthorized external model egress > 0
Document pipeline success < %99
```

## Pilot hedefleri

```text
Avukat kabul oranı: ≥ %80
Kaynağa ulaşma başarısı: ≥ %99
Kritik düzeltme oranı: sürümler boyunca düşüş
Belge pipeline başarı oranı: ≥ %99
```

Bu hedefler pilot verisine göre yeniden kalibre edilebilir; güvenlik ve kaynak bütünlüğü engelleri gevşetilemez.

---

# 28. Nihai MVP ürün kapsamı

## MVP’de bulunacak sınırlı fakat çalışan modüller

### Matter ve belge

- firma ve kullanıcı,
- matter oluşturma,
- matter bazlı erişim,
- belge yükleme,
- immutable original,
- OCR ve parsing,
- chain-of-custody,
- belge görüntüleme.

### Matter intelligence

- taraflar,
- kronoloji,
- iddialar ve savunmalar,
- delil matrisi,
- hukuki meseleler,
- kaynaklı matter Q&A.

### Hukuki araştırma

- güncel ve tarihsel mevzuat,
- yüksek mahkeme kararları,
- tarihsel geçerlilik filtresi,
- kaynaklı kısa araştırma notu,
- stale-source uyarısı.

### Taslak

- kontrollü bölüm taslağı,
- kaynak bağlantısı,
- citation doğrulaması,
- revision,
- insan onayı,
- DOCX/PDF export.

### Süre ve görev

- deadline trigger tespiti,
- hesaplama açıklaması,
- kaynak belge ve hukuk kuralı,
- insan doğrulaması,
- kontrollü görev/takvim çıktısı.

### Güvenlik ve operasyon

- MFA,
- audit,
- model-egress politikası,
- human approval,
- durable jobs,
- degraded mode,
- backup ve restore,
- soft delete/legal hold/purge.

## İlk sürümde yapılmayacaklar

- otomatik UYAP işlem gönderimi,
- ekran scraping,
- e-imza credential saklama,
- tam muhasebe ve faturalandırma,
- tam CRM,
- müvekkile denetimsiz hukuki tavsiye,
- kesin dava sonucu tahmini,
- otonom strateji kararı,
- insan onayı olmadan final dilekçe,
- otomatik kesin deadline,
- lisanssız hukuk içeriği toplama,
- gerçek zamanlı çoklu editör,
- ilk günden multi-tenant SaaS.

---

# 29. MESA geç bağlama, sürümleme ve güncelleme stratejisi

## 29.1 İlk fazlarda zorunlu MESA dependency yoktur

MESA-Law ilk kurulum ve testlerinde:

```text
INTELLIGENCE_ADAPTER=mock
MESA_ENABLED=false
```

ile çalışır. `pip install -e ../MESA` zorunlu değildir ve root dependency listesine MESA source package’ı eklenmez.

Bu karar şunları sağlar:

- MESA’daki yarım değişikliklerin hukuk ürününü bozmaması,
- agentin core’a kolayca çapraz bağımlılık kuramaması,
- canonical product testlerinin MESA olmadan çalışması,
- gerçek entegrasyon ihtiyacının ölçülerek belirlenmesi.

## 29.2 Contract snapshot ve capability manifest

Entegrasyon fazında repo şu dosyaları taşır:

```text
contracts/mesa/openapi-snapshot.json
contracts/mesa/required-capabilities.yaml
mesa-compatibility.yaml
```

Örnek:

```yaml
mesa:
  tested_version: "0.x.y"
  api_contract_hash: "sha256:..."
  minimum_version: "0.x.y"
  maximum_version: "<0.(x+1).0"

required_capabilities:
  - document_revision_ingest
  - source_locator_v2
  - temporal_filter_consistency
  - mutation_idempotency
  - rebuild
  - dataset_isolation
```

Version tek başına yeterli değildir; startup capability handshake zorunludur.

## 29.3 MESA gap analizi olmadan core değişmez

Agent veya geliştirici MESA’da değişiklik yapmadan önce:

1. failing contract test,
2. mevcut API’nin neden yetmediği,
3. adapter workaround’un neden kabul edilemez olduğu,
4. generic kullanım gerekçesi,
5. backward compatibility,
6. migration/rollback

raporlar.

Hukuka özel değişiklik generic core eksikliği olarak sunulamaz.

## 29.4 Production bağlantısı

Production:

```text
MESA-Law API
    ↓ HTTP
MESA V4 API
```

kullanır. Embedded adapter MVP kapsamı dışıdır. Bu sayede process, dependency ve storage ownership sınırları net kalır.

## 29.5 Upgrade akışı

```text
MESA release candidate
  ↓
Contract snapshot diff
  ↓
MESA-Law integration branch
  ↓
Mock/real parity + rebuild + legal benchmark
  ↓
Staging canary
  ↓
Tenant feature flag
  ↓
Production
```

Upgrade production’da otomatik yapılmaz. `main`, branch veya floating version kullanılmaz.

## 29.6 MCP sürümü ile product runtime ayrımı

MCP geliştirme ajanları için güncel olabilir; MESA-Law production test edilmiş eski MESA tag’inde kalabilir. MCP update hiçbir zaman product adapter target’ını otomatik yükseltmez.

## 29.7 CI matrisi

MESA entegrasyonundan önce:

```text
mock adapter
postgres lexical adapter
MESA disabled
```

MESA entegrasyonundan sonra:

```text
mock adapter
current MESA tag
next MESA release candidate
MESA unavailable/degraded
rebuild from canonical data
```

---

# 30. Canonical veri, yeniden üretim ve chain of custody sözleşmesi

## Canonical veri

```text
PostgreSQL
= canonical hukuk ve operasyon verisi

Object storage
= orijinal ve türetilmiş belgeler

MESA
= yeniden üretilebilir memory, assertion, vector ve graph intelligence
```

MESA verisi silinse bile PostgreSQL ve object storage kullanılarak matter veya tenant yeniden oluşturulabilir.

Her türetilmiş kayıtta:

```text
parser_version
ocr_engine_version
chunker_version
ontology_version
prompt_version
model_provider
model_name
model_version
pipeline_version
source_revision_id
```

tutulacaktır.

Operasyonlar:

```text
mesa-law rebuild-matter <matter_id>
mesa-law rebuild-tenant <tenant_id>
```

## Chain of custody

Orijinal belge değiştirilemez. Her dönüşüm ayrı türetilmiş artifact sayılır.

Tutulacak kayıtlar:

```text
original_file_hash
uploaded_by
uploaded_at
source_type
source_reference
document_revision
ocr_output_hash
conversion_history
digital_signature_status
view_events
download_events
export_events
```

Durumlar:

```text
ORIGINAL_VERIFIED
IMPORTED_COPY
OCR_DERIVED
SIGNATURE_VALID
SIGNATURE_INVALID
AUTHENTICITY_UNKNOWN
TAMPER_SUSPECTED
```

OCR metni hiçbir zaman orijinal belgenin yerine geçmez.

---

# 31. Ticari model, onboarding ve müşteri çıkışı

## İlk ticari paket

```text
Tek müşteriye özel kurulum ücreti
+ aylık bakım/abonelik
+ dahil kullanıcı kotası
+ dahil işlenen sayfa kotası
+ dahil depolama
+ model kullanım kotası
+ aşım ücretleri
+ özel entegrasyon bedeli
```

Depolama, model kullanımı ve özel entegrasyonlar ayrıca fiyatlandırılabilir.

## Onboarding

İlk müşteri kurulumunda:

- kullanıcılar aktarılır,
- matter listesi aktarılır,
- toplu belgeler yüklenir,
- duplicate kontrolü yapılır,
- bozuk dosya raporu üretilir,
- metadata/veri eşleme yapılır.

İlk 5–10 matter için zorunlu birlikte kurulum ve eğitim paketin standart parçası olmayacaktır; ihtiyaç halinde hizmet olarak sunulabilir.

## Offboarding

Müşteri ayrıldığında verilecekler:

- orijinal belgeler,
- matter listesi,
- temel metadata,
- timeline,
- iddia ve delil bağlantıları,
- taslaklar,
- audit kayıtları,
- provenance ilişkileri,
- silme sertifikası.

Standart vendor-neutral taşınabilir format ilk aşamada zorunlu değildir; ancak export dokümante ve doğrulanabilir olacaktır.

## Veri sahipliği

Müşteri:

- belgelerin,
- matter kayıtlarının,
- notların,
- düzeltmelerin,
- taslakların,
- firma hafızasının,
- onay kayıtlarının

sahibidir.

Ürün sahibi müşteri verisini serbest ortak veri olarak kullanamaz.

---

# 32. AI çıktı statüsü ve dış kullanım

Bütün AI çıktıları varsayılan olarak taslaktır.

```text
AI_GENERATED
SOURCE_CHECKED
ATTORNEY_REVIEWED
APPROVED_FOR_INTERNAL_USE
APPROVED_FOR_EXTERNAL_USE
```

Yalnız `APPROVED_FOR_EXTERNAL_USE` durumundaki içerik:

- müvekkile gönderilebilir,
- dışa aktarılabilir,
- resmî kullanıma hazırlanabilir.

UI genel bir uyarı vermekle yetinmeyecek; her paragraf ve sonuç için gerçek kaynak ve onay statüsünü gösterecektir.

---

# 33. Entegrasyon sırası

```text
1. Dosya ve klasör import
2. DOCX/PDF export
3. Takvim entegrasyonu
4. E-posta entegrasyonu
5. Word Add-in
6. DMS entegrasyonu
7. İzinli hukuk veri tabanı connector’ları
8. Resmî ve izinli UYAP entegrasyonu
9. Client Portal
```

MVP Draft Studio tek aktif editör ve revision lock ile başlayacaktır. Yjs/Hocuspocus benzeri gerçek zamanlı collaboration sonraki faza bırakılır.

---

# 34. Release, API ve migration sözleşmesi

Release akışı:

```text
Feature branch
→ Test
→ Legal benchmark
→ Release candidate
→ Staging
→ Canary
→ Production
```

Migration:

```text
Expand
→ Data migration
→ Compatibility period
→ Contract
```

Her release için:

- rollback paketi,
- database backup,
- schema compatibility kontrolü,
- MESA capability handshake,
- changelog

zorunludur.

İlk public API:

```text
/api/v1
```

Breaking değişiklik yeni major API sürümünde yapılacak ve en az 6 aylık deprecation penceresi uygulanacaktır.

---

# 35. Alt işleyen ve sağlayıcı şeffaflığı

Müşteriye şu bilgiler açıkça gösterilecektir:

```text
Sağlayıcı adı
Hizmet amacı
Gönderilen veri kategorisi
Barındırma bölgesi
Saklama politikası
Eğitimde kullanım durumu
Devre dışı bırakılabilirlik
```

Model sağlayıcısı veya alt işleyen değiştiğinde müşteri bilgilendirilecektir.

---

# 36. Açık kaynak, ticari lisans ve dependency sınırı

Repo ayrımı lisans düzeyinde de korunacaktır:

```text
MESA Core / SDK / MCP
→ ayrı açık kaynak veya source-available lisans kararı

MESA-Law application
→ proprietary/ticari ürün kodu

Legal source connectors
→ kaynak sağlayıcı sözleşmesine tabi ayrı modüller
```

Kesin lisans seçimi yayın öncesi ayrıca ADR ile belirlenecektir. CI aşağıdakileri zorunlu çalıştırır:

- SBOM üretimi,
- dependency license scan,
- yasaklı/uyumsuz lisans kontrolü,
- üçüncü taraf attribution dosyası,
- connector ve veri lisans manifest’i.

AGPL veya benzeri güçlü copyleft bağımlılıkları ürün içine alınmadan önce hukuk incelemesine tabi tutulur. Müşteri verisi, ürün kodu ve açık kaynak MESA katkıları birbirine karıştırılmaz.

---

# 37. Karar kayıtları — ADR listesi

Kodlama başlamadan aşağıdaki ADR’ler repo içinde tutulacaktır:

```text
ADR-001 İlk hedef müşteri ve genel dava analizi kapsamı
ADR-002 MVP’de dört ana workflow’un sınırlı birlikte sunulması
ADR-003 Canonical veri ve MESA rebuild sözleşmesi
ADR-004 Chain of custody ve belge bütünlüğü
ADR-005 Matter-local entity ve conflict index
ADR-006 Hukuk kaynağı lisans/güncellik politikası
ADR-007 Model sağlayıcı ve data-egress politikası
ADR-008 İnsan onayı ve sorumluluk matrisi
ADR-009 Avukat düzeltmesi, revision ve eğitim izni
ADR-010 Tek-tenant deployment ve veri yerleşimi
ADR-011 Backup, RPO/RTO ve degraded mode
ADR-012 Retention, legal hold, purge ve restore
ADR-013 Güvenlik operasyonu ve support access
ADR-014 Ticari paket, onboarding ve offboarding
ADR-015 Release, API ve migration politikası
ADR-016 Desteklenen hukuk kapsamı ve rule-pack sınırı
ADR-017 Deadline rule engine yönetişimi
ADR-018 Solo firm mode ve kritik işlem onayı
ADR-019 Bildirim ve eskalasyon
ADR-020 Kullanıcı/oturum yaşam döngüsü
ADR-021 Şifreleme anahtarı yönetimi
ADR-022 Güvenli dosya karantinası
ADR-023 Anonimleştirme ve benchmark kullanım izni
ADR-024 Retrieval completeness ve confidence gösterimi
ADR-025 Legal content operations ve snapshot release
ADR-026 Erişilebilirlik ve tarayıcı desteği
ADR-027 MESA/MESA-Law lisans sınırı
ADR-028 Tek-tenant’tan SaaS’a geçiş sözleşmesi
ADR-029 MESA late-binding ve iki evreli ürün geliştirme
ADR-030 Intelligence port, mock ve Postgres lexical fallback
ADR-031 UUIDv7, UTC ve source segment identity standardı
ADR-032 Transaction/outbox ve haricî çağrı sınırı
ADR-033 Idempotency, optimistic locking ve ETag
ADR-034 PostgreSQL job lease/dead-letter algoritması
ADR-035 FastAPI-owned OIDC session, cookie ve CSRF
ADR-036 RFC problem+json error taxonomy
ADR-037 Parser adapter ve canonical parsed artifact formatı
ADR-038 Feature flag ve tenant/matter config precedence
ADR-039 OpenAPI/Orval generated client standardı
ADR-040 Agent work-order, protected paths ve stop conditions
```

ADR’lerde karar, gerekçe, alternatifler, sonuçlar, güvenlik etkisi ve geri dönüş planı bulunacaktır.

---

# 38. Uygulama öncesi dış doğrulama gerektiren konular

Aşağıdaki başlıklar ürün yönü olarak karara bağlanmıştır; uygulama ayrıntıları seçilecek sağlayıcı ve sözleşmeye göre dış uzmanlarca doğrulanmalıdır:

1. Hukuk kaynaklarının kullanım, embedding, cache ve alıntı lisansları
2. Model sağlayıcılarının veri saklama ve eğitim sözleşmeleri
3. Hosting ve backup sağlayıcısının gerçek veri yerleşimi
4. Audit ve saklama sürelerinin hukuk danışmanı tarafından doğrulanması
5. Müşteri sözleşmesi, gizlilik eki ve veri işleme sözleşmesi
6. UYAP ve lisanslı hukuk veri tabanı entegrasyonlarının resmî izinleri
7. Dijital imza doğrulamasında kullanılacak güven hizmetleri
8. Silme sertifikası ve legal hold prosedürlerinin sözleşmesel karşılığı

Bu maddeler doğrulanmadan ilgili ticari özellik production’da etkinleştirilmemelidir.

---

# 39. Agent-optimize adım adım uygulama planı

Bu bölüm, bir coding agentin tek seferde bütün sistemi değiştirmesini engellemek ve her görevi doğrulanabilir bir teslimata dönüştürmek için bağlayıcı çalışma düzenidir.

## 39.1 Agent çalışma ilkeleri

1. Agent yalnız aktif work order kapsamındaki işi yapar.
2. Her work order tek bir ölçülebilir sonuç üretir.
3. Aynı work order ikiden fazla domain modülüne veya hem MESA hem MESA-Law reposuna dokunuyorsa bölünür.
4. Main branch üzerinde doğrudan değişiklik yapılmaz.
5. Master plan agent tarafından sessizce değiştirilmez; karar değişikliği ADR önerisi gerektirir.
6. Generated API client ve migration history elle yeniden yazılmaz.
7. Test silmek, assertion zayıflatmak veya skip eklemek çözüm sayılmaz.
8. MESA protected path’tir; Faz 5 gap analizi öncesinde değiştirilmez.
9. Gerçek müvekkil verisi, API key veya production secret agent context’ine verilmez.
10. Her görev sonunda handoff raporu üretilir.

## 39.2 Repository agent dosyaları

İlk commit aşağıdakileri oluşturur:

```text
AGENTS.md
CLAUDE.md
docs/agent/AGENT_RULES.md
docs/work-orders/WO-TEMPLATE.md
docs/handoffs/HANDOFF-TEMPLATE.md
docs/baselines/
```

Work order şablonu:

```markdown
# WO-XXX — Başlık

## Amaç
## Ön koşullar
## İzin verilen repo ve yollar
## Yasak yollar
## Değiştirilecek sözleşmeler
## Uygulama adımları
## Kabul kriterleri
## Çalıştırılacak testler
## Güvenlik/veri kontrolü
## Rollback
## Teslim çıktıları
```

Handoff:

```markdown
## Yapılanlar
## Değişen dosyalar
## Tasarım kararları
## Test komutları ve sonuçları
## Migration etkisi
## Güvenlik etkisi
## Bilinen eksikler
## Rollback
## Sonraki önerilen WO
```

## 39.3 Agent stop conditions

Aşağıdaki durumda agent kod yazmayı durdurup rapor üretir:

- destructive veya veri kaybettiren migration,
- master plandaki güvenlik minimumunu gevşetme,
- MESA core değişikliği gereksinimi,
- lisansı belirsiz dependency/veri kaynağı,
- production secret veya gerçek müşteri verisi görülmesi,
- cross-matter/tenant leakage,
- test baseline’ının beklenmedik biçimde düşmesi,
- API contract breaking change,
- iki geçerli mimari alternatif arasında ürün kararına ihtiyaç olması.

Agent durduğunda “nasıl olsa en mantıklısı” diyerek gizli karar vermez.

## 39.4 Branch ve commit standardı

```text
feat/wo-001-repo-foundation
fix/wo-0xx-...
chore/wo-0xx-...
```

Her work order için:

- preflight commit/status kaydı,
- implementation commit’leri,
- test/handoff commit’i,
- mümkünse squash edilebilir mantıksal commit yapısı

kullanılır.

## 39.5 WO-000 — Baseline ve freeze

**Repo:** MESA + MESA-Law boş repo

Yapılacaklar:

```bash
cd /home/yasin/Desktop/MESA
git status
git log -1 --oneline
uv sync --all-extras
uv run pytest
```

- MESA mevcut test/benchmark çıktısı kaydedilir.
- Baseline tag oluşturulur.
- MESA OpenAPI ve capability çıktısı snapshot alınır.
- MESA-Law private repo oluşturulur.
- Bu master plan `docs/plans/` altına konur.

**Yasak:** MESA source değişikliği.

**Kabul:** baseline raporu, tag, temiz git durumu ve work-order altyapısı.

## 39.6 WO-001 — Monorepo scaffold

**Repo:** MESA-Law

- uv Python workspace,
- pnpm workspace,
- `apps/web`, `apps/api`, `apps/worker`,
- root Makefile,
- lint/typecheck/test komutları,
- `.env.example`,
- AGENTS/CLAUDE kuralları.

Örnek komutlar:

```bash
uv init --bare
corepack enable
pnpm create next-app apps/web --ts --tailwind --eslint --app
```

**Kabul:** `make lint`, `make test`, `make dev-doctor` boş scaffold’da geçer.

## 39.7 WO-002 — Core Docker profili

`docker compose --profile core up -d` ile:

- PostgreSQL,
- MinIO,
- Redis,
- Keycloak,
- ClamAV,
- Caddy,
- legal-api/worker/web,
- OTel/Grafana stack

ayağa kalkar.

MESA servisi eklenmez.

**Kabul:** restart sonrası volume verisi korunur ve `make doctor` geçer.

## 39.8 WO-003 — Shared backend foundation

- settings/config precedence,
- UUIDv7,
- UTC clock abstraction,
- problem+json error handler,
- trace/correlation middleware,
- SQLAlchemy session,
- Alembic,
- audit base,
- idempotency store,
- optimistic locking utility.

**Kabul:** integration tests gerçek PostgreSQL üzerinde çalışır; hata envelope ve idempotency conflict test edilir.

## 39.9 WO-004 — Identity, tenant, matter ve RLS

- Keycloak dev realm,
- FastAPI session cookie ve CSRF,
- firm/user/matter/membership,
- role + matter membership + ethical wall,
- PostgreSQL RLS,
- session revoke ve MFA akışı.

**Kabul:** iki matter kullanıcısı API ve direct-SQL security testinde birbirinin verisini göremez.

## 39.10 WO-005 — Durable jobs/outbox

- `legal_jobs`, `legal_job_attempts`, `legal_outbox`,
- SKIP LOCKED lease,
- heartbeat,
- retry/backoff/jitter,
- dead-letter,
- idempotent handler contract.

**Kabul:** worker kill/restart testinde job kaybolmaz; duplicate delivery tek sonuç üretir.

## 39.11 WO-006 — Object storage ve chain of custody

- upload intent/presigned URL,
- quarantine state machine,
- ClamAV/MIME/archive checks,
- immutable key,
- object hash,
- document/revision canonical tables,
- view/download/export audit.

**Kabul:** overwrite mümkün değildir; source document upload olayından hash’e kadar izlenir.

## 39.12 WO-007 — Parser/OCR canonical artifacts

- parser interface,
- PyMuPDF PDF adapter,
- OCRmyPDF/Tesseract adapter,
- DOCX/XLSX/EML temel adapter,
- parsed JSONL artifact,
- source locator ve thumbnails,
- PostgreSQL FTS index.

**Kabul:** dijital ve scanned PDF’de doğru page/bbox açılır; reprocess yeni parsing revision üretir.

## 39.13 WO-008 — Intelligence port ve mock

- `MesaIntelligencePort`,
- contract models,
- MockMesaAdapter,
- PostgresLexicalAdapter,
- operation state,
- adapter feature flag.

Mock fixtures:

```text
success
pending
unavailable
projection_delayed
no_evidence_retrieved
source_set_incomplete
stale_source
```

**Kabul:** application services adapter sınıfını bilmez; aynı contract testleri mock ve lexical adapter’da çalışır.

## 39.14 WO-009 — Frontend shell ve canonical workflow

- login/MFA,
- matter list/create,
- upload/progress,
- PDF viewer,
- review shell,
- notifications,
- source status badges.

API client Orval ile üretilir.

**Kabul:** Playwright login → matter → upload → source open akışını tamamlar; MESA yoktur.

## 39.15 WO-010 — Mock intelligence UX

- timeline,
- claims/evidence,
- Q&A shell,
- research shell,
- degraded/incomplete source UI,
- no-evidence wording,
- confidence/support badges.

**Kabul:** bütün intelligence ekranları mock’un hata ve gecikme senaryolarını doğru gösterir.

## 39.16 WO-011 — Review, approval ve solo mode

- approve/reject/correct,
- revision/supersede,
- policy engine minimums,
- solo re-auth/cooling-off,
- external-use state,
- immutable audit.

**Kabul:** AI kaydı doğrudan verified olamaz; purge/external export politika dışı tamamlanamaz.

## 39.17 WO-012 — Legal source staging

- source manifest schema,
- versioned legal package format,
- current/historical legislation normalization,
- court decision metadata,
- anonymization workflow,
- snapshot release process.

Bu WO MESA ingestion yapmaz.

**Kabul:** golden legal package kendi validator’ından geçer; lisans ve hash metadata’sı eksiksizdir.

## 39.18 WO-013 — Benchmark governance

- train/dev/holdout ayrımı,
- annotation/adjudication schema,
- source/citation gold set,
- temporal version cases,
- leakage tests,
- benchmark version manifest.

**Kabul:** gizli holdout uygulama fixture’larından ve agent context’inden ayrıdır.

## 39.19 WO-014 — MESA gap analysis

**Repo:** öncelikle MESA-Law contract tests; MESA read-only.

- OpenAPI snapshot ile adapter spike,
- capability mapping,
- real MESA disposable environment,
- failing contract cases,
- SUPPORTED/WORKAROUND/CORE_CHANGE classification.

**Kabul:** core değişiklik listesi varsayım değil failing test ile kanıtlanır.

## 39.20 WO-015+ — Minimum MESA readiness

Her generic eksik ayrı work order’dır. Örnek:

```text
WO-015 SourceLocatorV2
WO-016 temporal filter consistency
WO-017 V4 idempotent ingestion
WO-018 capability/rebuild endpoint
```

**Repo:** MESA

Her biri:

- ayrı branch,
- public/generic API,
- backward compatibility,
- unit/integration/benchmark,
- changelog,
- release tag

üretir.

Hukuka özel resolver/prompt/ontology MESA’ya eklenmez.

## 39.21 WO-019 — MesaV4HttpAdapter

- production HTTP adapter,
- auth/service credential,
- capability handshake,
- error mapping,
- operation polling,
- timeout/retry/circuit breaker,
- idempotency propagation.

**Kabul:** mock ve real adapter contract testleri şema ve durum davranışında eşleşir.

## 39.22 WO-020 — MESA dataset binding ve rebuild

- matter-private dataset binding,
- legal-source dataset binding,
- document revision ingestion,
- canonical/MESA correlation,
- rebuild-matter/rebuild-tenant,
- purge/retraction mapping.

**Kabul:** disposable MESA store silinir ve canonical kaynaklardan yeniden kurulur.

## 39.23 WO-021 — Hukuk verilerini MESA’ya yükleme

Önce küçük golden set:

```text
2 mevzuat
2 tarihsel sürüm
20–50 yüksek mahkeme kararı
3 anonim matter
```

Başarılı benchmark sonrası kontrollü batch genişletilir.

**Kabul:** source snapshot, temporal query ve citation round-trip doğrulanır.

## 39.24 WO-022 — Legal extraction ve gerçek intelligence

- typed assertions,
- deterministic + model extraction,
- model/data-egress gateway,
- timeline/claims/evidence,
- retrieval completeness,
- correction/supersede.

**Kabul:** her assertion kaynaklı; başka matter’dan veri gelmez.

## 39.25 WO-023 — Source-grounded Q&A ve research

- query planner,
- hybrid retrieval,
- temporal/authority filters,
- citation verification,
- research memo,
- stale/degraded davranış.

**Kabul:** kaynak gerektiren final iddialarda citation kapsamı %100; approved fabricated citation sıfır.

## 39.26 WO-024 — Deadline rule packs

- versioned deterministic engine,
- legal source reference,
- holiday calendar version,
- POTENTIAL_DEADLINE fallback,
- approval ve notification.

**Kabul:** aktif rule pack olmayan alanda kesin deadline üretilmez.

## 39.27 WO-025 — Draft Studio

- Tiptap,
- single-editor lease,
- autosave revision,
- source chip,
- support validation,
- approval,
- DOCX/PDF export.

**Kabul:** external-use approval olmadan export/send yoktur.

## 39.28 WO-026 — CI, security ve release

Pipeline:

```text
lint/typecheck
unit/integration/RLS
frontend/Playwright
migration dry-run
mock adapter contract
real MESA contract
legal benchmark
SBOM/license/dependency/container scan
image signing
```

**Kabul:** herhangi bir kritik gate başarısızken release artifact production’a ilerlemez.

## 39.29 WO-027 — Tek-tenant pilot deployment

- ayrı DB/bucket/MESA root/key/secrets,
- DNS/TLS,
- backups,
- source snapshot,
- restore/rebuild tests,
- admin MFA,
- import ve smoke test,
- support access policy.

**Kabul:** production gate ve runbook tatbikatları tamamdır.

## 39.30 Agent başına önerilen görev boyutu

Agent görevi:

- tek bounded outcome,
- tercihen tek repo,
- tek migration grubu,
- tek API contract değişimi,
- testlerle doğrulanabilen kabul kriteri

olmalıdır.

Aşağıdakiler tek promptta verilmemelidir:

```text
“Bütün backend’i kur”
“Frontend’i tamamen yap”
“MESA’yı hukuk uygulamasına bağla ve veriyi doldur”
“Production’a hazırla”
```

Bunlar work order dizisine bölünmelidir.

---

# 40. Kurulum sonrası zorunlu runbook’lar

Production’a geçmeden şu runbook’lar yazılmış ve tatbik edilmiş olmalıdır:

```text
RB-001 Yeni tenant kurulumu
RB-002 Kullanıcı kapatma ve matter devir
RB-003 MESA rebuild
RB-004 Kaynak snapshot rollback
RB-005 Model rollback
RB-006 Database restore ve purge manifest replay
RB-007 Object storage restore
RB-008 SEV1 incident response
RB-009 Support access açma/kapatma
RB-010 Key rotation/revocation
RB-011 Legal hold ve purge
RB-012 Stale source/degraded mode
RB-013 OCR/parser toplu reprocess
RB-014 Tenant offboarding ve silme sertifikası
```

Her runbook; sorumlu rol, ön koşul, komut/adım, doğrulama, rollback ve audit çıktısını içermelidir.

---

# 41. Son boşluk taraması ve kesinleşen uygulama kararları

Son denetimde uygulayıcıya bırakılmış aşağıdaki kararlar kapatılmıştır:

|Alan|Kesin karar|
|---|---|
|MESA entegrasyon zamanı|Canonical ürün ve belge pipeline’ından sonra|
|İlk intelligence implementation|Mock + PostgreSQL lexical fallback|
|Production MESA iletişimi|HTTP V4 adapter; MCP/embedded değil|
|Core değişikliği|Failing contract test ve ADR olmadan yasak|
|ID|UUIDv7|
|Zaman|UTC storage, Europe/Istanbul gösterim|
|Transaction|External call DB transaction dışında, outbox sonrası|
|Command tekrarı|Idempotency-Key + request hash|
|Concurrency|version + ETag/If-Match; draft lease|
|Job queue|PostgreSQL SKIP LOCKED lease/dead-letter|
|Auth|FastAPI-managed OIDC session cookie + CSRF|
|API hata|application/problem+json|
|API client|OpenAPI → Orval generated|
|Parser|Adapter tabanlı; PyMuPDF/OCRmyPDF/Tesseract başlangıcı|
|Parsed canonical veri|Immutable JSONL/page artifacts + Postgres locator index|
|Config|Code default < deployment < tenant < matter; security floor sabit|
|Agent yönetimi|Work order, protected path, stop condition, handoff|
|Dev Compose|MESA’sız `core`, sonra opsiyonel `mesa` profili|

Bu plan kapsamında mimari veya kod mantığı açısından karar bekleyen kritik bir başlık bırakılmamıştır. Açık kalan konular yalnız dış sözleşme/hukuk doğrulaması, gerçek kaynak lisansları, seçilecek hosting/model sağlayıcısının kesin şartları ve pilot veriden çıkacak ölçümsel ayarlardır.

---

# Son değerlendirmem

Bu plan artık yalnız teknik bir mimari önerisi değildir. Ürün hedefi, desteklenen hukuk sınırı, kullanıcı tipi, hukuk veri kapsamı, MVP, deployment, canonical veri, chain of custody, güvenlik, insan onayı, model ve içerik yönetişimi, işletim, ticari model, release süreci ve adım adım kurulum sırası birlikte tanımlanmıştır.

Nihai yapı:

```text
MESA Core
= sektör bağımsız güvenilir memory, retrieval ve provenance platformu

MESA MCP Gateway
= Claude Code, Codex ve Antigravity için geliştirme/ajan adaptörü

MESA-Law Backend
= canonical hukuk domain’i, workflow, güvenlik ve ürün API’si; ilk fazlarda MESA’dan bağımsız

MESA-Law Frontend
= avukatın matter, belge, araştırma, review ve taslak çalışma alanı
```

Kesin veri sınırları:

```text
PostgreSQL
= canonical legal/operational data

S3 / MinIO
= immutable original ve derived documents

MESA
= geç bağlanan ve tamamen yeniden üretilebilir memory/assertion/vector/graph intelligence

MCP
= developer-agent integration; product runtime protocol değil
```

Kesin ürün sınırı:

```text
Hedef:
Bireysel avukatlar ve 3–20 kişilik küçük hukuk büroları

İlk hukuk alanı:
Genel dava dosyası analizi

MVP:
Dosya analizi
+ mevzuat/içtihat araştırması
+ sınırlı taslak
+ süre/görev çıkarımı
+ insan onayı

İlk deployment:
Müşteriye özel tek-tenant bulut

Başlangıç verisi:
Güncel/tarihsel mevzuat
+ yüksek mahkeme kararları
+ anonimleştirilmiş örnek dosyalar
```

En güçlü farklılaştırıcı:

> **Bir hukuk dosyasındaki her olgu, iddia, hukuki kural, süre ve taslak paragrafının hangi belgeye, hangi sayfaya, hangi mevzuat sürümüne, hangi model/pipeline sürümüne, hangi kullanıcı kararına ve hangi mutation zincirine dayandığını gösterebilmek; bunu matter izolasyonu, chain of custody ve insan onayı altında sürdürebilmektir.**

Bu revizyonla daha önce açık kalan kritik riskler kapatılmıştır:

- MESA verisinin nasıl yeniden üretileceği,
- orijinal belgenin nasıl korunacağı,
- entity’lerin matter’lar arasında nasıl izole edileceği,
- kimlerin hangi çıktıyı onaylayacağı,
- müşteri verisinin modele nasıl gönderileceği,
- model değişikliklerinin nasıl yayınlanacağı,
- kaynak güncelliği bozulduğunda sistemin ne yapacağı,
- yedek, restore, legal hold ve silmenin nasıl yönetileceği,
- sistem kısmi arızada nasıl çalışacağı,
- ilk müşterinin nasıl kurulacağı ve sistemden nasıl çıkarılacağı,
- pilotun hangi kalite kapılarıyla değerlendirileceği.

Bu mimariye ürün potansiyeli olarak **9.4/10**, mevcut MESA çekirdeğinden kontrollü biçimde üretilebilirlik açısından **7.5/10** veriyorum. Ana belirsizlik artık mimari değil; hukuk kaynak lisansları, gerçek pilot veri kalitesi, OCR/citation performansı ve pilot avukatların kullanıcı deneyimidir.