#!/usr/bin/env python3
"""
Migration script to convert from flat Firestore structure
to nested user-centric structure.

Old structure:
- /sessions/{sessionId}
- /topics/{topicId}
- /questions/{questionId}

New structure:
- /users/{userId}/sessions/{sessionId}
- /users/{userId}/topics/{topicId}
- /users/{userId}/topics/{topicId}/questions/{questionId}
- /users/{userId}/sessions/{sessionId}/messages/{messageId}
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict

# Add parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import firebase_admin
from firebase_admin import credentials, firestore

from core.monitoring.logger import get_logger

logger = get_logger("migration")


class FirestoreMigration:
    """Handles migration of Firestore data structure"""

    def __init__(self):
        # Initialize Firebase Admin SDK
        try:
            firebase_admin.get_app()
        except ValueError:
            # Use application default credentials
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": os.environ.get("GCLOUD_PROJECT")})

        self.db = firestore.client()
        self.dry_run = True

    async def run_migration(self):
        """Run all migration steps"""
        await self._migrate_topics()
        await self._migrate_questions()
        await self._migrate_sessions()
        await self._migrate_responses_to_messages()
        logger.info("Migration completed successfully")

    async def _migrate_topics(self):
        """Migrate topics from /topics/{topicId} to /users/{userId}/topics/{topicId}"""
        logger.info("Migrating topics...")

        # Get all topics from old structure
        topics_ref = self.db.collection("topics")
        topics_docs = topics_ref.stream()

        migrated_count = 0

        for topic_doc in topics_docs:
            topic_data = topic_doc.to_dict()
            topic_id = topic_doc.id
            user_uid = topic_data.get("ownerUid")

            if not user_uid:
                logger.warning("Topic %s has no ownerUid, skipping", topic_id)
                continue

            # Create new path: /users/{userId}/topics/{topicId}
            new_topic_ref = self.db.collection("users").document(user_uid).collection("topics").document(topic_id)

            if not self.dry_run:
                new_topic_ref.set(topic_data)
                logger.info("Migrated topic %s for user %s", topic_id, user_uid)
            else:
                logger.info("Would migrate topic %s for user %s", topic_id, user_uid)

            migrated_count += 1

        logger.info("Migrated %d topics", migrated_count)

    async def _migrate_questions(self):
        """
        Migrate questions from /questions/{questionId} to
        /users/{userId}/topics/{topicId}/questions/{questionId}
        """
        logger.info("Migrating questions...")

        # Get all questions from old structure
        questions_ref = self.db.collection("questions")
        questions_docs = questions_ref.stream()

        # We need to find the user for each question via the topic
        migrated_count = 0

        for question_doc in questions_docs:
            question_data = question_doc.to_dict()
            question_id = question_doc.id
            topic_id = question_data.get("topicId")

            if not topic_id:
                logger.warning("Question %s has no topicId, skipping", question_id)
                continue

            # Find the user who owns this topic
            user_uid = await self._find_topic_owner(topic_id)
            if not user_uid:
                logger.warning(
                    "Could not find owner for topic %s (question %s), skipping",
                    topic_id,
                    question_id,
                )
                continue

            # Create new path: /users/{userId}/topics/{topicId}/questions/{questionId}
            new_question_ref = (
                self.db.collection("users")
                .document(user_uid)
                .collection("topics")
                .document(topic_id)
                .collection("questions")
                .document(question_id)
            )

            if not self.dry_run:
                new_question_ref.set(question_data)
                logger.info(
                    "Migrated question %s for topic %s (user %s)",
                    question_id,
                    topic_id,
                    user_uid,
                )
            else:
                logger.info(
                    "Would migrate question %s for topic %s (user %s)",
                    question_id,
                    topic_id,
                    user_uid,
                )

            migrated_count += 1

        logger.info("Migrated %d questions", migrated_count)

    async def _migrate_sessions(self):
        """
        Migrate sessions from /sessions/{sessionId} to
        /users/{userId}/sessions/{sessionId}
        """
        logger.info("Migrating sessions...")

        # Get all sessions from old structure
        sessions_ref = self.db.collection("sessions")
        sessions_docs = sessions_ref.stream()

        migrated_count = 0

        for session_doc in sessions_docs:
            session_data = session_doc.to_dict()
            session_id = session_doc.id
            user_uid = session_data.get("userUid")

            if not user_uid:
                logger.warning(f"Session {session_id} has no userUid, skipping message migration")
                return

            # Clean up the session data - remove responses as they'll become
            # separate messages
            clean_session_data = {k: v for k, v in session_data.items() if k != "responses"}

            # Create new path: /users/{userId}/sessions/{sessionId}
            new_session_ref = self.db.collection("users").document(user_uid).collection("sessions").document(session_id)

            if not self.dry_run:
                new_session_ref.set(clean_session_data)
                logger.info("Migrated session %s for user %s", session_id, user_uid)
            else:
                logger.info("Would migrate session %s for user %s", session_id, user_uid)

            migrated_count += 1

        logger.info("Migrated %d sessions", migrated_count)

    async def _migrate_responses_to_messages(self):
        """Convert responses embedded in sessions to separate message subcollections"""
        logger.info("Converting responses to messages...")

        # Get all sessions from old structure to extract responses
        sessions_ref = self.db.collection("sessions")
        sessions_docs = sessions_ref.stream()

        migrated_count = 0

        for session_doc in sessions_docs:
            session_data = session_doc.to_dict()
            session_id = session_doc.id
            user_uid = session_data.get("userUid")
            responses = session_data.get("responses", [])

            if not user_uid or not responses:
                continue

            # Get question texts for embedding in messages
            question_texts = await self._get_question_texts_for_session(session_data, user_uid)

            # Convert each response to a message
            for i, response_data in enumerate(responses):
                question_id = response_data.get("questionId")
                question_text = question_texts.get(question_id, "Question text not available")

                message_data = {
                    "id": str(uuid.uuid4()),
                    "questionId": question_id,
                    "questionText": question_text,  # Embedded for efficiency
                    "answerText": response_data.get("answer", ""),
                    "score": response_data.get("score", 0),
                    "timestamp": response_data.get("timestamp", datetime.now()),
                }

                # Create path: /users/{userId}/sessions/{sessionId}/messages/{messageId}
                messages_ref = (
                    self.db.collection("users")
                    .document(user_uid)
                    .collection("sessions")
                    .document(session_id)
                    .collection("messages")
                )

                if not self.dry_run:
                    messages_ref.add(message_data)
                    migrated_count += 1
                else:
                    logger.info(
                        "Would create message for session %s, question %s",
                        session_id,
                        question_id,
                    )

        logger.info("Migrated %d responses to messages", migrated_count)

    async def _find_topic_owner(self, topic_id: str) -> str:
        """Find the user who owns a given topic"""
        try:
            topic_doc = self.db.collection("topics").document(topic_id).get()
            if topic_doc.exists:
                topic_data = topic_doc.to_dict()
                return topic_data.get("ownerUid")
        except Exception as e:
            logger.error("Error finding topic owner for %s: %s", topic_id, e)
        return None

    async def _get_question_texts_for_session(self, session_data: Dict[str, Any], user_uid: str) -> Dict[str, str]:
        """Get question texts for a session to embed in messages"""
        question_texts = {}
        question_ids = session_data.get("questionIds", [])
        topic_id = session_data.get("topicId")

        if not topic_id:
            return question_texts

        # Try to get questions from old structure first
        for question_id in question_ids:
            try:
                question_doc = self.db.collection("questions").document(question_id).get()
                if question_doc.exists:
                    question_data = question_doc.to_dict()
                    question_texts[question_id] = question_data.get("text", "Question text not available")
            except Exception as e:
                logger.warning("Could not get question text for %s: %s", question_id, e)
                question_texts[question_id] = "Question text not available"

        return question_texts

    async def _cleanup_old_collections(self):
        """Deletes old root-level collections after migration"""
        logger.info("Cleaning up old collections...")
        collections_to_delete = ["topics", "questions", "sessions"]

        for collection_name in collections_to_delete:
            logger.info(f"Deleting collection: {collection_name}")
            collection_ref = self.db.collection(collection_name)
            await self._delete_collection(collection_ref, batch_size=100)

    async def _delete_collection(self, collection_ref, batch_size):
        """Recursively delete a collection in batches"""
        docs = collection_ref.limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            logger.info(f"Deleting doc: {doc.id} from {collection_ref.path}")
            await doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return await self._delete_collection(collection_ref, batch_size)


async def main():
    """Main function to run migration"""
    migration = FirestoreMigration()
    await migration.run_migration()
    # Optional: cleanup old collections after verification
    # await migration._cleanup_old_collections()


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
