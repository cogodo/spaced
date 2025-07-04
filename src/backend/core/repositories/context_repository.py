from typing import List, Optional

from core.models.context import Context
from infrastructure.firebase import client as firebase_client


class ContextRepository:
    """Handles database operations for learning contexts"""

    def __init__(self, client=None):
        self.client = client or firebase_client

    async def get(self, context_id: str, user_uid: str) -> Optional[Context]:
        """Get a context by ID from the user's subcollection."""
        path = f"users/{user_uid}/contexts/{context_id}"
        data = await self.client.get_document(path)
        return Context(**data) if data else None

    async def create(self, context: Context) -> Context:
        """Create or overwrite a context document."""
        path = f"users/{context.userUid}/contexts/{context.chatId}"
        await self.client.set_document(path, context.dict())
        return context

    async def update(self, context_id: str, user_uid: str, data: dict) -> None:
        """Update a context document with new data."""
        path = f"users/{user_uid}/contexts/{context_id}"
        await self.client.update_document(path, data)

    async def delete(self, context_id: str, user_uid: str) -> None:
        """Delete a context document."""
        # Note: This does not handle subcollections like messages.
        # That logic would need to be orchestrated by a service if needed.
        path = f"users/{user_uid}/contexts/{context_id}"
        await self.client.delete_document(path)

    async def list_by_user(self, user_uid: str) -> List[Context]:
        """List all contexts for a given user."""
        path = f"users/{user_uid}/contexts"
        docs = await self.client.get_collection(path)
        return [Context(**doc) for doc in docs]
