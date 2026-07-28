import asyncio
from collections.abc import AsyncGenerator

import fitz  # PyMuPDF

try:
    import importlib.util
    HAS_TESSERACT = importlib.util.find_spec("pytesseract") is not None and importlib.util.find_spec("PIL") is not None
except ImportError:
    HAS_TESSERACT = False

from .base import DocumentParser


def _run_ocr_isolated(img_bytes: bytes) -> str:
    import io

    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(io.BytesIO(img_bytes)), lang='tur+eng')


class PyMuPDFParser(DocumentParser):
    async def parse(self, file_path_or_bytes: bytes) -> AsyncGenerator[dict]:
        loop = asyncio.get_running_loop()
        
        def _extract_all():
            doc = fitz.open(stream=file_path_or_bytes, filetype="pdf")
            pages_data = []
            for i, page in enumerate(doc):
                text = page.get_text("text")
                blocks = page.get_text("dict").get("blocks", [])
                
                # Filter text blocks
                text_blocks = [b for b in blocks if b.get("type") == 0]
                
                layout_blocks = []
                for b_idx, b in enumerate(text_blocks):
                    if "bbox" not in b:
                        continue
                    
                    block_text = ""
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            block_text += span.get("text", "") + " "
                        block_text += "\n"
                        
                    layout_blocks.append({
                        "id": f"b{b_idx}",
                        "bbox": b["bbox"],
                        "text": block_text.strip(),
                        "type": "block"
                    })
                
                # Text coverage heuristic
                page_area = page.rect.width * page.rect.height if page.rect else 0
                text_area = 0
                for b in text_blocks:
                    r = b.get("bbox")
                    if r:
                        text_area += (r[2] - r[0]) * (r[3] - r[1])
                
                text_coverage = (text_area / page_area) if page_area > 0 else 0
                
                ocr_used = False
                ocr_confidence = None
                
                # If text is extremely short or covers less than 2% of the page but there are images
                image_list = page.get_images(full=True)
                needs_ocr = False
                if not text.strip():
                    needs_ocr = True
                elif len(text.strip()) < 50 and len(image_list) > 0:
                    needs_ocr = True
                elif text_coverage < 0.02 and len(image_list) > 0:
                    needs_ocr = True

                if needs_ocr and HAS_TESSERACT:
                    try:
                        # Extract OCR logic to a standalone function for ProcessPoolExecutor isolation
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        
                        import concurrent.futures
                        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(_run_ocr_isolated, img_bytes)
                            ocr_text = future.result(timeout=60)
                            
                        # Combine or replace
                        if len(ocr_text.strip()) > len(text.strip()):
                            text = ocr_text
                            ocr_used = True
                            ocr_confidence = 0.85
                    except Exception:
                        pass
                
                if not text.strip():
                    text = f"[OCR Tara: Belge Sayfa {i+1} - Metin İçeriği Çıkarılamadı]"
                    ocr_used = True
                    ocr_confidence = 0.50
                
                pages_data.append({
                    "page_number": i + 1,
                    "text_content": text,
                    "layout_data": {"blocks": layout_blocks, "ocr_used": ocr_used, "ocr_confidence": ocr_confidence, "ocr_version": "tesseract-5" if ocr_used else None}
                })
            doc.close()
            return pages_data
            
        # Run blocking CPU-bound extraction in a thread
        pages = await loop.run_in_executor(None, _extract_all)
        
        for p in pages:
            yield p
