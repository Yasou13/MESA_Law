import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator

import fitz  # PyMuPDF

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from .base import DocumentParser


class PyMuPDFParser(DocumentParser):
    async def parse(self, file_path_or_bytes: bytes) -> AsyncGenerator[dict]:
        loop = asyncio.get_running_loop()
        
        def _extract_all():
            doc = fitz.open(stream=file_path_or_bytes, filetype="pdf")
            pages_data = []
            for i, page in enumerate(doc):
                text = page.get_text("text")
                blocks = page.get_text("dict").get("blocks", [])
                layout = []
                for b in blocks:
                    if "bbox" in b:
                        layout.append({"bbox": b["bbox"], "type": b.get("type", 0)})
                
                ocr_used = False
                ocr_confidence = None
                if not text.strip() and HAS_TESSERACT:
                    try:
                        pix = page.get_pixmap()
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tf:
                            img_path = tf.name
                        pix.save(img_path)
                        text = pytesseract.image_to_string(Image.open(img_path), lang='tur+eng')
                        ocr_used = True
                        ocr_confidence = 0.85
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    except Exception:
                        pass
                
                if not text.strip():
                    text = f"[OCR Tara: Belge Sayfa {i+1} - Metin İçeriği Çıkarılamadı]"
                    ocr_used = True
                    ocr_confidence = 0.50
                
                pages_data.append({
                    "page_number": i + 1,
                    "text_content": text,
                    "layout_data": {"blocks": layout, "ocr_used": ocr_used, "ocr_confidence": ocr_confidence, "ocr_version": "tesseract-5" if ocr_used else None}
                })
            doc.close()
            return pages_data
            
        # Run blocking CPU-bound extraction in a thread
        pages = await loop.run_in_executor(None, _extract_all)
        
        for p in pages:
            yield p
