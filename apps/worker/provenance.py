import hashlib
import re
import unicodedata
import uuid
from dataclasses import dataclass
from typing import Any

CHUNKING_VERSION = "mesa-law-chunker-v2"
MAX_CHUNK_CHARACTERS = 1200
VERIFIED_PDF = "VERIFIED_PDF"
VERIFIED_PDF_OCR = "VERIFIED_PDF_OCR"
LOW_PROVENANCE = "LOW_PROVENANCE"

_CHUNK_NAMESPACE = uuid.UUID("5389a2d8-2fcc-4cca-8c30-e7ddc2818791")


def normalize_text(value: str) -> str:
    """Return the canonical text representation used for persisted offsets."""
    normalized = unicodedata.normalize("NFKC", value).replace("\r\n", "\n")
    normalized = normalized.replace("\r", "\n").replace("\u00a0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", normalized)


def page_from_layout_blocks(
    blocks: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Build one normalized page and exact offsets from ordered PDF blocks."""
    text_parts: list[str] = []
    located_blocks: list[dict[str, Any]] = []
    cursor = 0
    for block in blocks:
        block_text = normalize_text(str(block.get("text", "")))
        if not block_text:
            continue
        if text_parts:
            text_parts.append("\n\n")
            cursor += 2
        start = cursor
        text_parts.append(block_text)
        cursor += len(block_text)
        located_blocks.append(
            {
                "id": block.get("id"),
                "text": block_text,
                "bbox": block.get("bbox"),
                "character_start": start,
                "character_end": cursor,
            }
        )
    return "".join(text_parts), located_blocks


def _split_range(text: str, start: int, end: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    cursor = start
    while cursor < end:
        while cursor < end and text[cursor].isspace():
            cursor += 1
        if cursor >= end:
            break
        boundary = min(cursor + MAX_CHUNK_CHARACTERS, end)
        if boundary < end:
            minimum = cursor + MAX_CHUNK_CHARACTERS // 2
            whitespace = max(
                text.rfind("\n", minimum, boundary),
                text.rfind(" ", minimum, boundary),
            )
            if whitespace > cursor:
                boundary = whitespace
        trimmed_end = boundary
        while trimmed_end > cursor and text[trimmed_end - 1].isspace():
            trimmed_end -= 1
        if trimmed_end > cursor:
            ranges.append((cursor, trimmed_end))
        cursor = max(boundary, cursor + 1)
    return ranges


@dataclass(frozen=True)
class ChunkSpec:
    id: str
    chunk_index: int
    text: str
    character_start: int
    character_end: int
    content_sha256: str
    bbox: dict[str, float] | None
    provenance_state: str


def build_chunks(
    *,
    page_text: str,
    page_number: int,
    content_identity: str,
    provenance_state: str,
    layout_blocks: list[dict[str, Any]] | None = None,
) -> list[ChunkSpec]:
    if not page_text:
        return []
    source_ranges = (
        [
            (
                int(block["character_start"]),
                int(block["character_end"]),
                block.get("bbox"),
            )
            for block in layout_blocks
            if block.get("character_start") is not None
            and block.get("character_end") is not None
        ]
        if layout_blocks
        else [(0, len(page_text), None)]
    )
    specs: list[ChunkSpec] = []
    for source_start, source_end, raw_bbox in source_ranges:
        for start, end in _split_range(page_text, source_start, source_end):
            chunk_text = page_text[start:end]
            digest = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            stable_name = f"{content_identity}:{page_number}:{start}:{end}:{digest}"
            bbox = None
            if raw_bbox and len(raw_bbox) == 4:
                bbox = {
                    "x0": float(raw_bbox[0]),
                    "y0": float(raw_bbox[1]),
                    "x1": float(raw_bbox[2]),
                    "y1": float(raw_bbox[3]),
                }
            specs.append(
                ChunkSpec(
                    id=str(uuid.uuid5(_CHUNK_NAMESPACE, stable_name)),
                    chunk_index=len(specs),
                    text=chunk_text,
                    character_start=start,
                    character_end=end,
                    content_sha256=digest,
                    bbox=bbox,
                    provenance_state=provenance_state,
                )
            )
    return specs
