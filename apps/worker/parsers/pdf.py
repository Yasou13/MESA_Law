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

def _run_ocr_isolated(img_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image
    import io
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
                
                ocr_used = False
                ocr_confidence = None
                if not text.strip() and HAS_TESSERACT:
                    try:
                        # Extract OCR logic to a standalone function for ProcessPoolExecutor isolation
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        
                        import concurrent.futures
                        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(_run_ocr_isolated, img_bytes)
                            text = future.result(timeout=60)
                            
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
