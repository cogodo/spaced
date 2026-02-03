import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import aiofiles.os

from core.monitoring.logger import get_logger

logger = get_logger("document_storage")

# Default storage path - can be overridden via environment variable
DEFAULT_STORAGE_PATH = "/var/spaced/documents"


class DocumentStorage:
    """
    Service for storing and managing document files on disk.

    Provides local storage for development with a structure that can
    be synced to cloud storage (S3/GCS) in production.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv("DOCUMENT_STORAGE_PATH", DEFAULT_STORAGE_PATH))
        logger.info(f"Document storage initialized at: {self.storage_path}")

    def _get_user_path(self, user_id: str) -> Path:
        """Get the storage path for a user"""
        return self.storage_path / user_id

    def _get_document_path(self, user_id: str, document_id: str) -> Path:
        """Get the storage path for a specific document"""
        return self._get_user_path(user_id) / document_id

    async def ensure_storage_exists(self) -> None:
        """Ensure the base storage directory exists"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def create_document_directory(self, user_id: str, document_id: str) -> Path:
        """
        Create a directory structure for a new document.

        Returns:
            Path to the document directory
        """
        doc_path = self._get_document_path(user_id, document_id)
        doc_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (doc_path / "original").mkdir(exist_ok=True)
        (doc_path / "pages").mkdir(exist_ok=True)

        return doc_path

    async def save_original_file(self, user_id: str, document_id: str, filename: str, content: bytes) -> Path:
        """
        Save the original uploaded file.

        Args:
            user_id: User's ID
            document_id: Document's ID
            filename: Original filename
            content: File content as bytes

        Returns:
            Path to the saved file
        """
        doc_path = self._get_document_path(user_id, document_id)
        original_dir = doc_path / "original"
        original_dir.mkdir(parents=True, exist_ok=True)

        file_path = original_dir / filename
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info(f"Saved original file: {file_path}")
        return file_path

    async def save_metadata(self, user_id: str, document_id: str, metadata: dict) -> None:
        """Save document metadata to JSON file"""
        doc_path = self._get_document_path(user_id, document_id)
        metadata_path = doc_path / "metadata.json"

        # Add timestamp
        metadata["savedAt"] = datetime.utcnow().isoformat()

        async with aiofiles.open(metadata_path, "w") as f:
            await f.write(json.dumps(metadata, indent=2, default=str))

    async def get_metadata(self, user_id: str, document_id: str) -> Optional[dict]:
        """Load document metadata from JSON file"""
        metadata_path = self._get_document_path(user_id, document_id) / "metadata.json"

        if not metadata_path.exists():
            return None

        async with aiofiles.open(metadata_path) as f:
            content = await f.read()
            return json.loads(content)

    def get_document_path(self, user_id: str, document_id: str) -> Path:
        """Get the path to a document's directory (synchronous for WarpGrep)"""
        return self._get_document_path(user_id, document_id)

    def get_user_documents_path(self, user_id: str) -> Path:
        """Get the path to all of a user's documents (for searching)"""
        return self._get_user_path(user_id)

    def get_content_path(self, user_id: str, document_id: str) -> Path:
        """Get the path to the parsed content.md file"""
        return self._get_document_path(user_id, document_id) / "content.md"

    def get_original_file_path(self, user_id: str, document_id: str) -> Optional[Path]:
        """Get the path to the original file if it exists"""
        original_dir = self._get_document_path(user_id, document_id) / "original"
        if original_dir.exists():
            files = list(original_dir.iterdir())
            if files:
                return files[0]
        return None

    async def document_exists(self, user_id: str, document_id: str) -> bool:
        """Check if a document directory exists"""
        return self._get_document_path(user_id, document_id).exists()

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        """
        Delete a document and all its files.

        Returns:
            True if deleted, False if didn't exist
        """
        doc_path = self._get_document_path(user_id, document_id)

        if not doc_path.exists():
            return False

        shutil.rmtree(doc_path)
        logger.info(f"Deleted document files: {doc_path}")
        return True

    async def list_user_documents(self, user_id: str) -> list[str]:
        """List all document IDs for a user based on filesystem"""
        user_path = self._get_user_path(user_id)

        if not user_path.exists():
            return []

        return [d.name for d in user_path.iterdir() if d.is_dir()]

    async def get_storage_stats(self, user_id: str) -> dict:
        """Get storage statistics for a user"""
        user_path = self._get_user_path(user_id)

        if not user_path.exists():
            return {"documentCount": 0, "totalSizeBytes": 0}

        total_size = 0
        doc_count = 0

        for doc_dir in user_path.iterdir():
            if doc_dir.is_dir():
                doc_count += 1
                for file_path in doc_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size

        return {"documentCount": doc_count, "totalSizeBytes": total_size}


# Singleton instance
_storage_instance: Optional[DocumentStorage] = None


def get_document_storage() -> DocumentStorage:
    """Get the singleton DocumentStorage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DocumentStorage()
    return _storage_instance
