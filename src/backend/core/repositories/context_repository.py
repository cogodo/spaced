import logging
from typing import List, Optional

from google.cloud.firestore_v1 import DocumentSnapshot

from core.models.context import Context
from infrastructure.firebase import get_firestore_client

logger = logging.getLogger(__name__)


class ContextRepository:
    """Handles database operations for learning contexts"""

    def __init__(self):
        self.db = get_firestore_client()

    async def get(self, context_id: str, user_uid: str) -> Optional[Context]:
        """Get a context by ID from the user's subcollection."""
        doc_ref = self.db.collection("users").document(user_uid).collection("contexts").document(context_id)
        snapshot: DocumentSnapshot = doc_ref.get()
        if snapshot.exists:
            return Context(**snapshot.to_dict())
        return None

    async def create(self, context: Context) -> Context:
        """Create or overwrite a context document."""
        doc_ref = self.db.collection("users").document(context.userUid).collection("contexts").document(context.chatId)
        doc_ref.set(context.dict())
        return context

    def update(self, chat_id: str, user_uid: str, data: dict) -> None:
        """Update an existing context document."""
        logger.info(f"Updating context {chat_id} for user {user_uid}")
        doc_ref = self.db.collection("users").document(user_uid).collection("contexts").document(chat_id)
        try:
            doc_ref.update(data)
            logger.info(f"Successfully updated context {chat_id}")
        except Exception as e:
            logger.error(f"Failed to update context {chat_id}: {e}", exc_info=True)
            raise

    async def delete(self, context_id: str, user_uid: str) -> None:
        """Delete a context document."""
        doc_ref = self.db.collection("users").document(user_uid).collection("contexts").document(context_id)
        doc_ref.delete()

    async def list_by_user(self, user_uid: str) -> List[Context]:
        """List all contexts for a given user."""
        collection_ref = self.db.collection("users").document(user_uid).collection("contexts")
        snapshots = collection_ref.stream()
        return [Context(**doc.to_dict()) for doc in snapshots]
