#!/usr/bin/env python3
"""
Test script to verify the FSRS spaced repetition system is working properly.
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import Question, Topic
from core.monitoring.logger import get_logger
from core.services import QuestionService, SessionService, TopicService
from core.services.fsrs_service import FSRSService

logger = get_logger("fsrs_test")


class FSRSSystemTest:
    def __init__(self):
        self.topic_service = TopicService()
        self.question_service = QuestionService()
        self.session_service = SessionService()
        self.fsrs_service = FSRSService()
        self.test_user_uid = "dev-user-123"

    async def run_fsrs_tests(self):
        """Run comprehensive tests of the FSRS system"""
        logger.info("Starting FSRS system tests for user: %s", self.test_user_uid)

        try:
            # Test 1: Create topic and questions
            topic = await self._create_test_topic()
            await self._create_test_questions(topic)

            # Test 2: Run learning session with good performance
            await self._run_learning_session(topic, good_performance=True)

            # Test 3: Verify FSRS parameters were updated
            await self._verify_fsrs_update(topic.id)

            # Test 4: Test topic review status endpoints
            await self._test_review_endpoints()

            logger.info("All FSRS tests passed successfully!")
            return True

        except Exception as e:
            logger.error("FSRS test failed: %s", e)
            return False

    async def _create_test_topic(self):
        """Create a test topic for FSRS testing"""
        logger.info("Creating test topic...")

        topic = await self.topic_service.create_topic(
            user_uid=self.test_user_uid,
            name="FSRS Test Topic - Spanish Vocabulary",
            description="A test topic for FSRS spaced repetition testing",
        )

        logger.info("Created topic: %s", topic.id)
        return topic

    async def _create_test_questions(self, topic: Topic):
        """Create test questions for the topic"""
        logger.info("Creating test questions...")

        questions = []
        spanish_words = [
            ("Hola", "Hello"),
            ("Gracias", "Thank you"),
            ("Por favor", "Please"),
            ("¿Cómo estás?", "How are you?"),
            ("Me llamo", "My name is"),
        ]

        for i, (spanish, english) in enumerate(spanish_words):
            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=f"What does '{spanish}' mean in English?",
                type="short_answer",
                difficulty=1,
                metadata={"correct_answer": english, "test": True},
            )

            # Save question using repository
            saved_question = await self.question_service.repository.create(question, self.test_user_uid)
            questions.append(saved_question)

        # Update topic question bank
        await self.topic_service.update_question_bank(topic.id, self.test_user_uid, [q.id for q in questions])

        logger.info("Created %d test questions", len(questions))
        return questions

    async def _run_learning_session(self, topic: Topic, good_performance: bool = True):
        """Run a complete learning session"""
        logger.info(
            "Running learning session with %s performance...",
            "good" if good_performance else "poor",
        )

        # Start session
        session = await self.session_service.start_session(user_uid=self.test_user_uid, topic_id=topic.id)

        # Answer all 5 questions in the session
        for i in range(5):
            # Get current question
            _, current_question = await self.session_service.get_current_question(session.id, self.test_user_uid)

            if not current_question:
                break

            # Simulate answer based on performance level
            if good_performance:
                answer = "Excellent answer that demonstrates understanding"
            else:
                answer = "Poor answer"

            # Submit response
            result = await self.session_service.submit_response(session.id, self.test_user_uid, answer)

            logger.info("Question %d: Score %d/5", i + 1, result["score"])

            # Break if session is complete
            if result.get("isComplete"):
                logger.info("Session completed after %d questions", i + 1)
                break

        return session

    async def _verify_fsrs_update(self, topic_id: str):
        """Verify that FSRS parameters were updated correctly"""
        logger.info("Verifying FSRS parameter updates...")

        # Get updated topic
        topic = await self.topic_service.get_topic(topic_id, self.test_user_uid)

        # Check that FSRS fields are populated
        assert topic.lastReviewedAt is not None, "Last reviewed date should be set"
        assert topic.nextReviewAt is not None, "Next review date should be set"

        # Check that next review is in the future
        assert topic.nextReviewAt > datetime.now(), "Next review should be in the future"

        # Check FSRS params have been updated
        assert topic.fsrsParams.repetition > 0, "Repetition count should be increased"

        # Calculate expected interval based on performance
        days_until_review = (topic.nextReviewAt - datetime.now()).days
        logger.info("Next review in %d days", days_until_review)

        assert days_until_review >= 1, "Review interval should be at least 1 day"

        logger.info("FSRS parameters updated correctly:")
        logger.info("- Ease: %.2f", topic.fsrsParams.ease)
        logger.info("- Interval: %d days", topic.fsrsParams.interval)
        logger.info("- Repetitions: %d", topic.fsrsParams.repetition)
        logger.info("- Next review: %s", topic.nextReviewAt)

    async def _test_review_endpoints(self):
        """Test the new review status endpoints"""
        logger.info("Testing review status endpoints...")

        # Import the endpoint functions
        from api.v1.endpoints.topics import (
            get_review_statistics,
            get_todays_reviews,
            get_topics_with_review_status,
        )

        # Mock current user
        mock_user = {"uid": self.test_user_uid}

        # Test topics with review status
        topics_with_status = await get_topics_with_review_status(self.test_user_uid, mock_user)
        assert len(topics_with_status) >= 1, "Should have at least one topic with status"

        topic_status = topics_with_status[0]
        assert "reviewUrgency" in topic_status, "Should have review urgency"
        assert "retentionProbability" in topic_status, "Should have retention probability"
        assert "fsrsParams" in topic_status, "Should have FSRS parameters"

        logger.info("Topic review status: %s", topic_status["reviewUrgency"])

        # Test today's reviews
        todays_reviews = await get_todays_reviews(self.test_user_uid, mock_user)
        assert "totalDue" in todays_reviews, "Should have total due count"
        assert "overdue" in todays_reviews, "Should have overdue list"
        assert "dueToday" in todays_reviews, "Should have due today list"

        logger.info(
            "Due today: %d, Overdue: %d",
            len(todays_reviews["dueToday"]),
            len(todays_reviews["overdue"]),
        )

        # Test review statistics
        stats = await get_review_statistics(self.test_user_uid, mock_user)
        assert "totalTopics" in stats, "Should have total topics count"
        assert "averageRetention" in stats, "Should have average retention"
        assert "studyStreak" in stats, "Should have study streak"

        logger.info(
            "Study statistics - Topics: %d, Retention: %.2f",
            stats["totalTopics"],
            stats["averageRetention"],
        )

        logger.info("Review endpoints working correctly!")

    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up FSRS test data...")

        try:
            # Get and delete test topics
            topics = await self.topic_service.get_user_topics(self.test_user_uid)
            for topic in topics:
                if "Test Topic" in topic.name:
                    # Delete questions first
                    questions = await self.question_service.get_topic_questions(topic.id, self.test_user_uid)
                    for question in questions:
                        await self.question_service.repository.delete(question.id, self.test_user_uid, topic.id)

                    # Delete topic
                    await self.topic_service.repository.delete(topic.id, self.test_user_uid)
                    logger.info("Deleted test topic: %s", topic.name)

            logger.info("FSRS test cleanup completed")

        except Exception as e:
            logger.warning("FSRS test cleanup failed (this is usually OK): %s", e)


async def main():
    """Main test function"""
    test = FSRSSystemTest()

    print("FSRS Spaced Repetition System Test")
    print("===================================")
    print("This will test the complete FSRS learning and review system.")
    print("")

    try:
        success = await test.run_fsrs_tests()

        if success:
            print("\n✅ All FSRS tests passed! Spaced repetition system is working " "correctly.")
            print("\nKey features tested:")
            print("  - Topic & question creation")
            print("- Topic completion updates FSRS parameters")
            print("- Next review dates are calculated")
            print("- Review status endpoints work")
            print("- Study statistics are generated")
        else:
            print("\n❌ Some FSRS tests failed. Check the logs above.")

        cleanup = input("\nClean up test data? (y/N): ")
        if cleanup.lower() == "y":
            await test.cleanup_test_data()
            print("FSRS test data cleaned up.")

    except Exception as e:
        print(f"\n❌ FSRS test execution failed: {e}")
        logger.error("FSRS test execution failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
