import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from starlette.concurrency import run_in_threadpool

from core.models import Document, DocumentListItem, DocumentStatus, ParsedDocument
from core.monitoring.logger import get_logger
from core.parsers import get_parser
from core.parsers.factory import ALLOWED_TYPES, MAX_FILE_SIZE, is_supported_type
from core.repositories import DocumentRepository
from infrastructure.storage import get_document_storage

logger = get_logger("document_service")


class DocumentServiceError(Exception):
    """Base exception for document service errors"""

    pass


class DocumentService:
    """Service for document upload, processing, and management"""

    def __init__(self):
        self.repository = DocumentRepository()
        self.storage = get_document_storage()

    async def upload_document(
        self,
        user_uid: str,
        filename: str,
        content: bytes,
        content_type: str,
        topic_id: Optional[str] = None,
    ) -> Document:
        """
        Upload and begin processing a document.

        Args:
            user_uid: User's ID
            filename: Original filename
            content: File content as bytes
            content_type: MIME type of the file
            topic_id: Optional topic to link the document to

        Returns:
            Document record with processing status

        Raises:
            DocumentServiceError: If validation fails
        """
        # Validate file type
        if not is_supported_type(content_type):
            raise DocumentServiceError(
                f"Unsupported file type: {content_type}. Supported types: {', '.join(ALLOWED_TYPES.keys())}"
            )

        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise DocumentServiceError(f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB")

        # Generate document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Create document record
        document = Document(
            id=document_id,
            ownerUid=user_uid,
            name=Path(filename).stem,  # Filename without extension
            originalFilename=filename,
            mimeType=content_type,
            fileSize=len(content),
            status=DocumentStatus.UPLOADING,
            linkedTopics=[topic_id] if topic_id else [],
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )

        # Save to Firestore
        await run_in_threadpool(self.repository.create, document)

        # Save original file to storage
        await self.storage.ensure_storage_exists()
        await self.storage.create_document_directory(user_uid, document_id)
        original_path = await self.storage.save_original_file(user_uid, document_id, filename, content)

        # Update status to processing
        await run_in_threadpool(
            self.repository.update_status,
            document_id,
            user_uid,
            DocumentStatus.PROCESSING,
        )

        # Process the document
        try:
            parsed = await self._process_document(user_uid, document_id, original_path, content_type)

            # Update with success
            await run_in_threadpool(
                self.repository.update_status,
                document_id,
                user_uid,
                DocumentStatus.READY,
                None,
                parsed.pageCount,
                parsed.wordCount,
            )

            # Update storage path
            storage_path = str(self.storage.get_document_path(user_uid, document_id))
            await run_in_threadpool(
                self.repository.update,
                document_id,
                user_uid,
                {"storagePath": storage_path},
            )

            document.status = DocumentStatus.READY
            document.pageCount = parsed.pageCount
            document.wordCount = parsed.wordCount
            document.storagePath = storage_path

            logger.info(
                f"Document processed successfully: {document_id}",
                extra={"pageCount": parsed.pageCount, "wordCount": parsed.wordCount},
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Document processing failed: {error_msg}")

            await run_in_threadpool(
                self.repository.update_status,
                document_id,
                user_uid,
                DocumentStatus.ERROR,
                error_msg,
            )

            document.status = DocumentStatus.ERROR
            document.error = error_msg

        return document

    async def _process_document(
        self, user_uid: str, document_id: str, file_path: Path, content_type: str
    ) -> ParsedDocument:
        """Parse a document and save the extracted content"""
        parser = get_parser(content_type)
        if not parser:
            raise DocumentServiceError(f"No parser available for {content_type}")

        output_dir = self.storage.get_document_path(user_uid, document_id)

        # Parse the document
        parsed = await parser.parse(file_path, output_dir)

        # Save metadata
        await self.storage.save_metadata(
            user_uid,
            document_id,
            {
                "pageCount": parsed.pageCount,
                "wordCount": parsed.wordCount,
                "slideCount": parsed.slideCount,
                "contentType": content_type,
            },
        )

        return parsed

    async def get_document(self, document_id: str, user_uid: str) -> Optional[Document]:
        """Get a document by ID"""
        return await run_in_threadpool(self.repository.get_by_id, document_id, user_uid)

    async def list_documents(self, user_uid: str) -> List[DocumentListItem]:
        """List all documents for a user"""
        documents = await run_in_threadpool(self.repository.list_by_owner, user_uid)

        return [
            DocumentListItem(
                id=doc.id,
                name=doc.name,
                status=doc.status,
                pageCount=doc.pageCount,
                createdAt=doc.createdAt,
            )
            for doc in documents
        ]

    async def list_topic_documents(self, user_uid: str, topic_id: str) -> List[DocumentListItem]:
        """List all documents linked to a topic"""
        documents = await run_in_threadpool(self.repository.list_by_topic, user_uid, topic_id)

        return [
            DocumentListItem(
                id=doc.id,
                name=doc.name,
                status=doc.status,
                pageCount=doc.pageCount,
                createdAt=doc.createdAt,
            )
            for doc in documents
        ]

    async def delete_document(self, document_id: str, user_uid: str) -> bool:
        """
        Delete a document and all its files.

        Returns:
            True if deleted, False if not found
        """
        # Check if document exists
        document = await self.get_document(document_id, user_uid)
        if not document:
            return False

        # Delete files from storage
        await self.storage.delete_document(user_uid, document_id)

        # Delete from Firestore
        await run_in_threadpool(self.repository.delete, document_id, user_uid)

        logger.info(f"Deleted document: {document_id}")
        return True

    async def link_to_topic(self, document_id: str, user_uid: str, topic_id: str) -> bool:
        """Link a document to a topic"""
        document = await self.get_document(document_id, user_uid)
        if not document:
            return False

        await run_in_threadpool(self.repository.link_to_topic, document_id, user_uid, topic_id)
        return True

    async def unlink_from_topic(self, document_id: str, user_uid: str, topic_id: str) -> bool:
        """Unlink a document from a topic"""
        document = await self.get_document(document_id, user_uid)
        if not document:
            return False

        await run_in_threadpool(self.repository.unlink_from_topic, document_id, user_uid, topic_id)
        return True

    def get_document_content_path(self, user_uid: str, document_id: str) -> Path:
        """Get the path to the parsed content.md file (for WarpGrep)"""
        return self.storage.get_content_path(user_uid, document_id)

    def get_user_documents_path(self, user_uid: str) -> Path:
        """Get the path to all user documents (for WarpGrep searching)"""
        return self.storage.get_user_documents_path(user_uid)
