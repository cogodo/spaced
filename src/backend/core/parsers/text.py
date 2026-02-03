from pathlib import Path

from bs4 import BeautifulSoup

from core.models import ParsedDocument
from core.monitoring.logger import get_logger

from .base import BaseParser

logger = get_logger("text_parser")


class TextParser(BaseParser):
    """Parser for text-based documents (MD, TXT, HTML)"""

    async def parse(self, file_path: Path, output_dir: Path) -> ParsedDocument:
        """
        Parse a text document.

        For text files, we mostly just copy the content.
        For HTML, we extract text and convert to markdown-ish format.
        """
        logger.info(f"Parsing text file: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        suffix = file_path.suffix.lower()

        if suffix == ".html":
            content = self._html_to_text(content)

        # Clean up the content
        content = self._clean_text(content)
        word_count = self.count_words(content)

        # For text files, we estimate "pages" based on word count
        # Roughly 300 words per page
        estimated_pages = max(1, word_count // 300)

        # Save content
        content_file = output_dir / "content.md"
        content_file.write_text(content, encoding="utf-8")

        logger.info(f"Parsed text file: ~{estimated_pages} pages, {word_count} words")

        return ParsedDocument(
            pageCount=estimated_pages,
            wordCount=word_count,
        )

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text with basic structure"""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Convert headers to markdown
        for i in range(1, 7):
            for header in soup.find_all(f"h{i}"):
                prefix = "#" * i
                header.replace_with(f"\n{prefix} {header.get_text().strip()}\n")

        # Convert lists
        for ul in soup.find_all("ul"):
            items = ul.find_all("li")
            text = "\n".join(f"- {li.get_text().strip()}" for li in items)
            ul.replace_with(f"\n{text}\n")

        for ol in soup.find_all("ol"):
            items = ol.find_all("li")
            text = "\n".join(f"{i+1}. {li.get_text().strip()}" for i, li in enumerate(items))
            ol.replace_with(f"\n{text}\n")

        # Convert paragraphs
        for p in soup.find_all("p"):
            p.replace_with(f"\n{p.get_text().strip()}\n")

        # Get text
        text = soup.get_text()
        return text

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace more than 2 consecutive newlines with 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip trailing whitespace from lines
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()
