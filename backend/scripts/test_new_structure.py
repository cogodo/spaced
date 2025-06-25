#!/usr/bin/env python3
"""
Test script to verify the new Firestore structure is working properly.
This creates sample data and tests all major operations.
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.services import SessionService, TopicService, QuestionService
from core.models import Topic, Question, Session
from core.monitoring.logger import get_logger

logger = get_logger("structure_test")


class StructureTest:
    def __init__(self):
        self.topic_service = TopicService()
        self.question_service = QuestionService()
        self.session_service = SessionService()
        self.test_user_uid = "dev-user-123"
        
    async def run_all_tests(self):
        """Run comprehensive tests of the new structure"""
        logger.info("Starting structure tests for user: %s", self.test_user_uid)
        
        try:
            # Test 1: Topic creation and retrieval
            topic = await self._test_topic_operations()
            
            # Test 2: Question generation
            questions = await self._test_question_operations(topic)
            
            # Test 3: Session management
            session = await self._test_session_operations(topic)
            
            # Test 4: Message handling
            await self._test_message_operations(session, questions[0])
            
            logger.info("All tests passed successfully!")
            return True
            
        except Exception as e:
            logger.error("Test failed: %s", e)
            return False
    
    async def _test_topic_operations(self):
        """Test topic creation and retrieval"""
        logger.info("Testing topic operations...")
        
        # Create a test topic
        topic = await self.topic_service.create_topic(
            user_uid=self.test_user_uid,
            name="Test Topic - Python Programming",
            description="A test topic for Python programming concepts"
        )
        
        logger.info("Created topic: %s", topic.id)
        
        # Retrieve topics for user
        user_topics = await self.topic_service.get_user_topics(self.test_user_uid)
        assert len(user_topics) >= 1, "Should have at least one topic"
        
        # Retrieve specific topic
        retrieved_topic = await self.topic_service.get_topic(topic.id, self.test_user_uid)
        assert retrieved_topic is not None, "Should retrieve the created topic"
        assert retrieved_topic.name == topic.name, "Topic name should match"
        
        logger.info("Topic operations test passed")
        return topic
    
    async def _test_question_operations(self, topic: Topic):
        """Test question generation and retrieval"""
        logger.info("Testing question operations...")
        
        # Note: This would normally call OpenAI, so we'll create manual questions
        questions = []
        for i in range(5):
            question = Question(
                id=str(uuid.uuid4()),
                topicId=topic.id,
                text=f"Test question {i+1}: What is a Python {['variable', 'function', 'class', 'module', 'package'][i]}?",
                type="short_answer",
                difficulty=1,
                metadata={"test": True}
            )
            
            # Save question using repository
            saved_question = await self.question_service.repository.create(question, self.test_user_uid)
            questions.append(saved_question)
        
        logger.info("Created %d test questions", len(questions))
        
        # Retrieve questions for topic
        topic_questions = await self.question_service.get_topic_questions(topic.id, self.test_user_uid)
        assert len(topic_questions) == 5, f"Should have 5 questions, got {len(topic_questions)}"
        
        # Update topic question bank
        await self.topic_service.update_question_bank(
            topic.id, 
            self.test_user_uid,
            [q.id for q in questions]
        )
        
        logger.info("Question operations test passed")
        return questions
    
    async def _test_session_operations(self, topic: Topic):
        """Test session creation and management"""
        logger.info("Testing session operations...")
        
        # Start a new session
        session = await self.session_service.start_session(
            user_uid=self.test_user_uid,
            topic_id=topic.id
        )
        
        logger.info("Created session: %s", session.id)
        
        # Get current question
        retrieved_session, current_question = await self.session_service.get_current_question(
            session.id, 
            self.test_user_uid
        )
        
        assert retrieved_session is not None, "Should retrieve session"
        assert current_question is not None, "Should have a current question"
        assert retrieved_session.id == session.id, "Session IDs should match"
        
        logger.info("Session operations test passed")
        return session
    
    async def _test_message_operations(self, session: Session, question: Question):
        """Test message creation and retrieval"""
        logger.info("Testing message operations...")
        
        # Submit a response (creates a message)
        result = await self.session_service.submit_response(
            session.id,
            self.test_user_uid,
            "A variable is a container for storing data values in Python."
        )
        
        assert "score" in result, "Should return a score"
        assert "feedback" in result, "Should return feedback"
        
        # Get session messages
        messages = await self.session_service.get_session_messages(session.id, self.test_user_uid)
        assert len(messages) >= 1, "Should have at least one message"
        
        # Check message structure
        message = messages[0]
        assert hasattr(message, 'questionId'), "Message should have questionId"
        assert hasattr(message, 'questionText'), "Message should have embedded questionText"
        assert hasattr(message, 'answerText'), "Message should have answerText"
        assert hasattr(message, 'score'), "Message should have score"
        
        logger.info("Message operations test passed")
        
        # Test skip question
        skip_result = await self.session_service.skip_question(session.id, self.test_user_uid)
        assert "score" in skip_result, "Skip should return result"
        
        # Get messages again (should have skip message)
        messages_after_skip = await self.session_service.get_session_messages(session.id, self.test_user_uid)
        assert len(messages_after_skip) > len(messages), "Should have more messages after skip"
        
        logger.info("Skip question test passed")
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("Cleaning up test data...")
        
        try:
            # Get all user topics and delete them
            topics = await self.topic_service.get_user_topics(self.test_user_uid)
            for topic in topics:
                # Delete questions first
                questions = await self.question_service.get_topic_questions(topic.id, self.test_user_uid)
                for question in questions:
                    await self.question_service.repository.delete(question.id, self.test_user_uid, topic.id)
                
                # Delete topic
                await self.topic_service.repository.delete(topic.id, self.test_user_uid)
            
                         # Get all user sessions and delete them - use topic service to get topics with sessions
            topics = await self.topic_service.get_user_topics(self.test_user_uid)
            for topic in topics:
                # Find any sessions for this topic
                try:
                    existing_sessions = await self.session_service.repository.list_by_user_and_topic(self.test_user_uid, topic.id)
                    for session in existing_sessions:
                        # Delete messages first
                        try:
                            messages = await self.session_service.get_session_messages(session.id, self.test_user_uid)
                            for message in messages:
                                await self.session_service.repository.delete_message(
                                    self.test_user_uid, session.id, message.id
                                )
                        except:
                            pass  # Messages might not exist
                        
                        # Delete session
                        await self.session_service.repository.delete(session.id, self.test_user_uid)
                except:
                    pass  # Sessions might not exist
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.warning("Cleanup failed (this is usually OK for tests): %s", e)


async def main():
    """Main test function"""
    test = StructureTest()
    
    print("Firestore New Structure Test")
    print("============================")
    print("This will test all major operations with the new nested structure.")
    print("")
    
    try:
        success = await test.run_all_tests()
        
        if success:
            print("\n✅ All tests passed! The new structure is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the logs above.")
            
        cleanup = input("\nClean up test data? (y/N): ")
        if cleanup.lower() == 'y':
            await test.cleanup_test_data()
            print("Test data cleaned up.")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        logger.error("Test execution failed", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 