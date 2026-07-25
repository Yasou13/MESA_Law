import fitz  # PyMuPDF
import asyncio
from typing import AsyncGenerator
from .base import DocumentParser

class PyMuPDFParser(DocumentParser):
    async def parse(self, file_path_or_bytes: bytes) -> AsyncGenerator[dict, None]:
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
                
                pages_data.append({
                    "page_number": i + 1,
                    "text_content": text,
                    "layout_data": {"blocks": layout}
                })
            doc.close()
            return pages_data
            
        # Run blocking CPU-bound extraction in a thread
        pages = await loop.run_in_executor(None, _extract_all)
        
        for p in pages:
            yield p
