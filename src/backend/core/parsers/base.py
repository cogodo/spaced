from abc import ABC, abstractmethod
from pathlib import Path

from core.models import ParsedDocument


class BaseParser(ABC):
    """Base class for document parsers"""

    @abstractmethod
    async def parse(self, file_path: Path, output_dir: Path) -> ParsedDocument:
        """
        Parse a document and save extracted content.

        Args:
            file_path: Path to the input file
            output_dir: Directory to save parsed output

        Returns:
            ParsedDocument with metadata about the parsed content
        """
        pass

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        return len(text.split())
