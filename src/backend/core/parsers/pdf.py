from pathlib import Path

import pymupdf

from core.models import ParsedDocument
from core.monitoring.logger import get_logger

from .base import BaseParser

logger = get_logger("pdf_parser")


class PDFParser(BaseParser):
    """Parser for PDF documents using PyMuPDF"""

    async def parse(self, file_path: Path, output_dir: Path) -> ParsedDocument:
        """
        Parse a PDF document and extract text to markdown.

        Creates:
        - content.md: Full document as searchable markdown
        - pages/page_XXX.md: Individual page files for large docs
        - metadata.json: Document metadata
        """
        logger.info(f"Parsing PDF: {file_path}")

        doc = pymupdf.open(str(file_path))
        total_word_count = 0
        full_content = []

        # Create pages directory
        pages_dir = output_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()

            # Clean up the text
            page_text = self._clean_text(page_text)

            if page_text.strip():
                # Save individual page
                page_file = pages_dir / f"page_{page_num + 1:03d}.md"
                page_content = f"# Page {page_num + 1}\n\n{page_text}"
                page_file.write_text(page_content, encoding="utf-8")

                # Add to full content
                full_content.append(f"## Page {page_num + 1}\n\n{page_text}")
                total_word_count += self.count_words(page_text)

        doc.close()

        # Save full document
        content_file = output_dir / "content.md"
        full_text = "\n\n---\n\n".join(full_content)
        content_file.write_text(full_text, encoding="utf-8")

        logger.info(f"Parsed PDF: {len(full_content)} pages, {total_word_count} words")

        return ParsedDocument(
            pageCount=len(full_content),
            wordCount=total_word_count,
        )

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace while preserving paragraph breaks
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Strip trailing whitespace
            line = line.rstrip()
            cleaned_lines.append(line)

        # Join and clean up multiple blank lines
        text = "\n".join(cleaned_lines)

        # Replace more than 2 consecutive newlines with 2
        import re

        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
