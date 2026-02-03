from datetime import datetime
from typing import List, Optional

from core.models import Document, DocumentStatus
from core.monitoring.logger import get_logger
from infrastructure.firebase import get_firestore_client

logger = get_logger("document_repository")


class DocumentRepository:
    """Repository for document metadata in Firestore"""

    def __init__(self):
        self.db = get_firestore_client()

    def _get_user_documents_collection(self, user_uid: str):
        """Get user's documents collection reference"""
        return self.db.collection("users").document(user_uid).collection("documents")

    def create(self, document: Document) -> Document:
        """Create a new document record under user's subcollection"""
        doc_ref = self._get_user_documents_collection(document.ownerUid).document(document.id)
        doc_ref.set(document.model_dump())
        logger.info(f"Created document record: {document.id}")
        return document

    def get_by_id(self, document_id: str, user_uid: str) -> Optional[Document]:
        """Get document by ID from user's subcollection"""
        doc = self._get_user_documents_collection(user_uid).document(document_id).get()
        if doc.exists:
            return Document(**doc.to_dict())
        return None

    def list_by_owner(self, user_uid: str) -> List[Document]:
        """Get all documents for a user from their subcollection"""
        docs = self._get_user_documents_collection(user_uid).order_by("createdAt", direction="DESCENDING").stream()

        documents = []
        for doc in docs:
            try:
                documents.append(Document(**doc.to_dict()))
            except Exception as e:
                logger.warning(f"Failed to parse document {doc.id}: {e}")
                continue

        return documents

    def list_by_topic(self, user_uid: str, topic_id: str) -> List[Document]:
        """Get all documents linked to a specific topic"""
        docs = self._get_user_documents_collection(user_uid).where("linkedTopics", "array_contains", topic_id).stream()

        documents = []
        for doc in docs:
            try:
                documents.append(Document(**doc.to_dict()))
            except Exception as e:
                logger.warning(f"Failed to parse document {doc.id}: {e}")
                continue

        return documents

    def update(self, document_id: str, user_uid: str, updates: dict) -> None:
        """Update document fields in user's subcollection"""
        updates["updatedAt"] = datetime.utcnow()
        doc_ref = self._get_user_documents_collection(user_uid).document(document_id)
        doc_ref.update(updates)
        logger.debug(f"Updated document {document_id}")

    def update_status(
        self,
        document_id: str,
        user_uid: str,
        status: DocumentStatus,
        error: Optional[str] = None,
        page_count: Optional[int] = None,
        word_count: Optional[int] = None,
    ) -> None:
        """Update document processing status"""
        updates = {
            "status": status.value,
            "updatedAt": datetime.utcnow(),
        }

        if error is not None:
            updates["error"] = error

        if status == DocumentStatus.READY:
            updates["processedAt"] = datetime.utcnow()
            if page_count is not None:
                updates["pageCount"] = page_count
            if word_count is not None:
                updates["wordCount"] = word_count

        self.update(document_id, user_uid, updates)
        logger.info(f"Updated document {document_id} status to {status.value}")

    def link_to_topic(self, document_id: str, user_uid: str, topic_id: str) -> None:
        """Link a document to a topic"""
        from google.cloud.firestore import ArrayUnion

        doc_ref = self._get_user_documents_collection(user_uid).document(document_id)
        doc_ref.update(
            {
                "linkedTopics": ArrayUnion([topic_id]),
                "updatedAt": datetime.utcnow(),
            }
        )
        logger.info(f"Linked document {document_id} to topic {topic_id}")

    def unlink_from_topic(self, document_id: str, user_uid: str, topic_id: str) -> None:
        """Unlink a document from a topic"""
        from google.cloud.firestore import ArrayRemove

        doc_ref = self._get_user_documents_collection(user_uid).document(document_id)
        doc_ref.update(
            {
                "linkedTopics": ArrayRemove([topic_id]),
                "updatedAt": datetime.utcnow(),
            }
        )
        logger.info(f"Unlinked document {document_id} from topic {topic_id}")

    def delete(self, document_id: str, user_uid: str) -> None:
        """Delete a document record"""
        self._get_user_documents_collection(user_uid).document(document_id).delete()
        logger.info(f"Deleted document record: {document_id}")
