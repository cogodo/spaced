"""
Question Generation Service for Phase 4: Question → Conversation → Scoring Architecture

This service generates, stores, and manages question banks for topics using LLM generation
and Firebase storage, enabling efficient question-based learning conversations.
"""

import json
import uuid
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from .firebase_service import FirebaseService
from .tools import get_llm
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """Service for generating and managing topic question banks"""
    
    def __init__(self):
        self.firebase_service = FirebaseService()
    
    async def generate_topic_questions(self, topic: str, topic_context: str = "") -> List[Dict]:
        """
        Generate 25-30 high-quality learning questions for a topic using LLM
        
        Args:
            topic: The topic name (e.g., "Python Functions")
            topic_context: Additional context about the topic
            
        Returns:
            List of question objects with metadata
        """
        try:
            logger.info(f"Generating questions for topic: {topic}")
            
            # Build comprehensive prompt for question generation
            prompt = self._build_question_generation_prompt(topic, topic_context)
            
            # Generate questions using LLM
            llm = get_llm()
            messages = [
                SystemMessage(content="You are an expert educational content creator specializing in conversational learning questions."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            response_text = response.content
            
            # Parse and validate the response
            questions = self._parse_question_response(response_text)
            
            # Add metadata to each question
            enhanced_questions = self._enhance_questions_with_metadata(questions, topic)
            
            logger.info(f"Generated {len(enhanced_questions)} questions for topic: {topic}")
            return enhanced_questions
            
        except Exception as e:
            logger.error(f"Error generating questions for topic {topic}: {e}")
            return []
    
    def _build_question_generation_prompt(self, topic: str, topic_context: str) -> str:
        """Build comprehensive prompt for LLM question generation"""
        
        return f"""
Generate 25-30 high-quality learning questions for the topic: "{topic}"

{f"Additional Context: {topic_context}" if topic_context else ""}

QUESTION VARIETY REQUIREMENTS:
- Conceptual understanding (what, why, define, explain)
- Procedural knowledge (how to, demonstrate, walk through)
- Application scenarios (when, where, use cases)
- Problem-solving challenges (troubleshoot, debug, optimize)
- Connection and comparison questions (relate to, contrast with)
- Example and explanation requests (give examples, show me)
- Analysis and evaluation (analyze, critique, assess)

DIFFICULTY DISTRIBUTION:
- 8-10 Easy questions (foundational concepts, basic definitions)
- 12-15 Medium questions (application, analysis, connections)
- 5-7 Hard questions (synthesis, evaluation, complex problem-solving)

CONVERSATION DESIGN PRINCIPLES:
Each question should:
1. Be conversational and engaging (avoid quiz-like tone)
2. Allow for natural follow-up discussion
3. Test genuine understanding, not memorization
4. Be appropriate for extended back-and-forth dialogue
5. Encourage explanation and examples from the student
6. Create opportunities for teaching moments

EXAMPLES OF GOOD CONVERSATIONAL QUESTIONS:
- "Can you walk me through what a Python function is and why you'd want to use one?"
- "I'm curious about your understanding of loops - how would you explain them to someone new?"
- "Let's talk about debugging - what's your approach when code doesn't work as expected?"

AVOID:
- Yes/no questions without follow-up potential
- Pure memorization questions
- Overly technical jargon without explanation opportunity
- Questions with single "correct" answers

Return ONLY a valid JSON array of questions with this exact structure:
[
    {{
        "id": "unique_identifier",
        "text": "conversational question text",
        "difficulty": "easy|medium|hard", 
        "question_type": "conceptual|procedural|application|analysis|synthesis|evaluation",
        "expected_follow_ups": ["potential follow-up areas", "teaching opportunities"],
        "learning_objectives": ["what this question assesses"]
    }}
]

Generate exactly 25-30 questions covering the full spectrum of understanding for: {topic}
"""

    def _parse_question_response(self, response: str) -> List[Dict]:
        """Parse and validate the LLM response containing questions"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")
                
            json_str = response[json_start:json_end]
            questions = json.loads(json_str)
            
            # Validate structure
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
                
            # Validate each question has required fields
            required_fields = ['id', 'text', 'difficulty', 'question_type']
            validated_questions = []
            
            for i, q in enumerate(questions):
                if not isinstance(q, dict):
                    logger.warning(f"Question {i} is not a dictionary, skipping")
                    continue
                    
                # Check required fields
                if not all(field in q for field in required_fields):
                    logger.warning(f"Question {i} missing required fields, skipping")
                    continue
                    
                # Validate difficulty
                if q['difficulty'] not in ['easy', 'medium', 'hard']:
                    logger.warning(f"Question {i} has invalid difficulty, defaulting to medium")
                    q['difficulty'] = 'medium'
                    
                validated_questions.append(q)
            
            logger.info(f"Validated {len(validated_questions)} questions from {len(questions)} generated")
            return validated_questions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing question response: {e}")
            return []
    
    def _enhance_questions_with_metadata(self, questions: List[Dict], topic: str) -> List[Dict]:
        """Add metadata and ensure consistent structure for questions"""
        enhanced = []
        
        for q in questions:
            # Ensure unique ID
            if not q.get('id') or not isinstance(q['id'], str):
                q['id'] = f"q_{topic.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
            
            # Add metadata
            q.update({
                'topic': topic,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'used': False,
                'usage_count': 0,
                'last_used': None,
                'average_conversation_length': None,
                'performance_data': {}
            })
            
            # Ensure optional fields exist
            q.setdefault('expected_follow_ups', [])
            q.setdefault('learning_objectives', [])
            
            enhanced.append(q)
        
        return enhanced

    async def store_questions_in_firebase(self, user_id: str, topic_id: str, questions: List[Dict]) -> bool:
        """
        Store generated questions in Firebase under user's topic question bank
        
        Args:
            user_id: User identifier
            topic_id: Topic identifier (should be URL-safe)
            questions: List of question objects
            
        Returns:
            Success status
        """
        try:
            if not questions:
                logger.warning(f"No questions to store for topic {topic_id}")
                return False
                
            # Store in Firebase: users/{user_id}/question_banks/{topic_id}/questions/{question_id}
            questions_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
            )
            
            # Prepare topic metadata
            topic_data = {
                'topic_name': questions[0].get('topic', topic_id),
                'question_count': len(questions),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'questions_used': 0,
                'questions_remaining': len(questions),
                'last_accessed': None
            }
            
            # Store topic metadata
            questions_ref.set(topic_data)
            
            # Store individual questions in subcollection
            questions_collection = questions_ref.collection('questions')
            
            batch = self.firebase_service._db.batch()
            for question in questions:
                question_ref = questions_collection.document(question['id'])
                batch.set(question_ref, question)
            
            # Commit batch write
            batch.commit()
            
            logger.info(f"Stored {len(questions)} questions for topic {topic_id} (user: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error storing questions for topic {topic_id}: {e}")
            return False

    async def get_unused_questions(self, user_id: str, topic_id: str, limit: int = 7) -> List[Dict]:
        """
        Retrieve unused questions for a topic
        
        Args:
            user_id: User identifier
            topic_id: Topic identifier
            limit: Maximum number of questions to return
            
        Returns:
            List of unused question objects
        """
        try:
            questions_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
                .collection('questions')
            )
            
            # Query for unused questions
            query = questions_ref.where('used', '==', False).limit(limit)
            docs = query.stream()
            
            questions = []
            for doc in docs:
                question_data = doc.to_dict()
                question_data['id'] = doc.id  # Ensure ID is present
                questions.append(question_data)
            
            logger.info(f"Retrieved {len(questions)} unused questions for topic {topic_id}")
            return questions
            
        except Exception as e:
            logger.error(f"Error retrieving unused questions for topic {topic_id}: {e}")
            return []

    async def mark_question_used(self, user_id: str, topic_id: str, question_id: str) -> bool:
        """
        Mark a question as used (or delete it based on preference)
        
        Args:
            user_id: User identifier  
            topic_id: Topic identifier
            question_id: Question identifier
            
        Returns:
            Success status
        """
        try:
            question_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
                .collection('questions')
                .document(question_id)
            )
            
            # Update question as used
            question_ref.update({
                'used': True,
                'last_used': datetime.now(timezone.utc).isoformat(),
                'usage_count': 1  # Could be incremented if reusing questions
            })
            
            # Update topic metadata
            topic_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
            )
            
            topic_ref.update({
                'questions_used': 1,
                'questions_remaining': -1,
                'last_accessed': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Marked question {question_id} as used for topic {topic_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking question {question_id} as used: {e}")
            return False

    async def get_next_question(self, user_id: str, topic_id: str) -> Optional[Dict]:
        """
        Get the next unused question for a topic
        
        Args:
            user_id: User identifier
            topic_id: Topic identifier
            
        Returns:
            Next question object or None if no questions available
        """
        unused_questions = await self.get_unused_questions(user_id, topic_id, limit=1)
        return unused_questions[0] if unused_questions else None

    async def ensure_topic_has_questions(self, user_id: str, topic_id: str, topic_name: str, topic_context: str = "") -> bool:
        """
        Ensure a topic has questions in the question bank, generate if needed
        
        Args:
            user_id: User identifier
            topic_id: Topic identifier (URL-safe)
            topic_name: Human-readable topic name
            topic_context: Additional context for question generation
            
        Returns:
            Success status
        """
        try:
            # Check if topic already has questions
            existing_questions = await self.get_unused_questions(user_id, topic_id, limit=1)
            
            if existing_questions:
                logger.info(f"Topic {topic_id} already has questions")
                return True
            
            # Check if topic exists but all questions are used
            topic_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
            )
            
            topic_doc = topic_ref.get()
            if topic_doc.exists:
                topic_data = topic_doc.to_dict()
                if topic_data.get('questions_remaining', 0) == 0:
                    logger.info(f"All questions used for topic {topic_id}, generating new ones")
                else:
                    logger.info(f"Topic {topic_id} has questions available")
                    return True
            
            # Generate new questions
            logger.info(f"Generating questions for new topic: {topic_name}")
            questions = await self.generate_topic_questions(topic_name, topic_context)
            
            if not questions:
                logger.error(f"Failed to generate questions for topic {topic_name}")
                return False
            
            # Store questions in Firebase
            success = await self.store_questions_in_firebase(user_id, topic_id, questions)
            
            if success:
                logger.info(f"Successfully initialized question bank for topic {topic_name} ({len(questions)} questions)")
            else:
                logger.error(f"Failed to store questions for topic {topic_name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error ensuring topic {topic_id} has questions: {e}")
            return False

    def create_topic_id(self, topic_name: str) -> str:
        """Create a URL-safe topic ID from topic name"""
        return topic_name.lower().replace(' ', '_').replace('-', '_') 