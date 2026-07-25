from abc import ABC, abstractmethod
from typing import AsyncGenerator

class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, file_path_or_bytes: bytes) -> AsyncGenerator[dict, None]:
        """
        Parses a document and yields pages one by one.
        Yields dict with:
        - page_number: int (1-indexed)
        - text_content: str
        - layout_data: dict (containing blocks, bboxes, etc.)
        """
        pass
        # AsyncGenerator cannot just have `pass` if it's meant to be typing compatible,
        # but as an abstract base it's fine.
        yield {}
