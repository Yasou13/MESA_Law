import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import fitz
from apps.worker.provenance import normalize_text, page_from_layout_blocks

from .base import DocumentParser


def parse_pdf_bytes(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract stable per-page text and layout without inventing OCR output."""
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pages: list[dict[str, Any]] = []
        for page_index, page in enumerate(document):
            raw_blocks = page.get_text("dict").get("blocks", [])
            layout_blocks: list[dict[str, Any]] = []
            for block_index, block in enumerate(raw_blocks):
                if block.get("type") != 0 or "bbox" not in block:
                    continue
                spans: list[str] = []
                for line in block.get("lines", []):
                    line_text = "".join(
                        str(span.get("text", "")) for span in line.get("spans", [])
                    )
                    if line_text:
                        spans.append(line_text)
                block_text = normalize_text("\n".join(spans))
                if block_text:
                    layout_blocks.append(
                        {
                            "id": f"b{block_index}",
                            "bbox": list(block["bbox"]),
                            "text": block_text,
                            "type": "block",
                        }
                    )

            page_text, located_blocks = page_from_layout_blocks(layout_blocks)
            pages.append(
                {
                    "page_number": page_index + 1,
                    "text_content": page_text,
                    "layout_data": {
                        "blocks": located_blocks,
                        "ocr_required": not bool(page_text),
                        "ocr_used": False,
                        "ocr_version": None,
                    },
                }
            )
        return pages
    finally:
        document.close()


class PyMuPDFParser(DocumentParser):
    async def parse(self, file_path_or_bytes: bytes) -> AsyncGenerator[dict[str, Any]]:
        pages = await asyncio.to_thread(parse_pdf_bytes, file_path_or_bytes)
        for page in pages:
            yield page
