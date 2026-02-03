from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Document(BaseModel):
    id: str
    ownerUid: str
    name: str
    originalFilename: str
    mimeType: str
    fileSize: int
    status: DocumentStatus = DocumentStatus.UPLOADING

    # Processing results
    pageCount: Optional[int] = None
    wordCount: Optional[int] = None
    error: Optional[str] = None

    # Links
    linkedTopics: List[str] = []
    storagePath: Optional[str] = None  # Path where parsed files are stored

    # Timestamps
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    processedAt: Optional[datetime] = None


class ParsedDocument(BaseModel):
    """Result of parsing a document"""

    pageCount: int = 0
    wordCount: int = 0
    slideCount: Optional[int] = None  # For PPTX


class SearchResult(BaseModel):
    """Result from document search"""

    file: str
    content: str
    documentId: str
    relevanceScore: Optional[float] = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""

    documentId: str
    status: DocumentStatus
    filename: str


class DocumentListItem(BaseModel):
    """Simplified document for list view"""

    id: str
    name: str
    status: DocumentStatus
    pageCount: Optional[int]
    createdAt: Optional[datetime]
