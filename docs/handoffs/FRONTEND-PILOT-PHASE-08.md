# Phase 8: Belge Merkezi ve Viewer Handoff

## 1. İlgili Testler ve Exit Code
Manuel kod incelemesi yapıldı, frontend'e `Document Center` ve `Document Viewer` sayfaları eklendi, hooklar başarıyla entegre edildi.

## 2. Değişen Dosyalar
- `apps/api/routers/documents.py` (Yeni: `GET /api/v1/documents` ve `GET /api/v1/documents/{document_id}`)
- `apps/web/src/app/(protected)/documents/page.tsx` (Tüm dokümanları ve statülerini listeleyen sayfa)
- `apps/web/src/app/(protected)/documents/[id]/page.tsx` (İlgili dokümanın detayını ve varsayılan tarayıcı PDF/Iframe viewer'ı açan sayfa)
- `apps/web/src/components/Sidebar.tsx` (Navigasyona Documents eklendi)

## 3. Eklenen Migration
Yok.

## 4. API Sözleşmesi Etkisi
İki yeni okuma uç (endpoint) eklendi. Frontend bu uçları kullanarak liste ve detay gösterimi sağlamaktadır.

## 5. Güvenlik Etkisi
`setup_tenant_context` aracılığıyla hem liste hem de doküman detayı API'da filtreleniyor.
Karantina (`quarantined`) veya virüslü (`infected`) dokümanlar için URL üretimi backend tarafından engelleniyor ve frontend'de bu durumlara özel uyarılar (viewer gizlenerek) devreye giriyor.

## 6. Bilinen Kalan Açıklar
Phase 9 ve sonrası.

## 7. Rollback Adımları
`git checkout -- apps/api/routers/documents.py apps/web/src/components/Sidebar.tsx`
`rm -rf apps/web/src/app/\(protected\)/documents`

## 8. Sonraki Faz
Phase 9: OCR Hata Akışı
