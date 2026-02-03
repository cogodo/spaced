from typing import Optional

from .base import BaseParser
from .pdf import PDFParser
from .pptx import PPTXParser
from .text import TextParser

# Mapping of MIME types to parser classes
MIME_TYPE_PARSERS = {
    "application/pdf": PDFParser,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": PPTXParser,
    "text/markdown": TextParser,
    "text/plain": TextParser,
    "text/html": TextParser,
}

# Allowed MIME types with their extensions
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/markdown": ".md",
    "text/plain": ".txt",
    "text/html": ".html",
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PAGES = 500  # For PDFs


def get_parser(mime_type: str) -> Optional[BaseParser]:
    """
    Get the appropriate parser for a given MIME type.

    Args:
        mime_type: The MIME type of the file

    Returns:
        A parser instance or None if the type is not supported
    """
    parser_class = MIME_TYPE_PARSERS.get(mime_type)
    if parser_class:
        return parser_class()
    return None


def is_supported_type(mime_type: str) -> bool:
    """Check if a MIME type is supported for parsing"""
    return mime_type in ALLOWED_TYPES
