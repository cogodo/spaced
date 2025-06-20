import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from core.models import Session, Response, Topic
from core.repositories import SessionRepository
from core.services.topic_service import TopicService
from core.services.question_service import QuestionService
from core.services.scoring_service import ScoringService
from core.services.fsrs_service import FSRSService
from infrastructure.redis import RedisSessionManager


class SessionService:
    def __init__(self):
        self.repository = SessionRepository()
        self.topic_service = TopicService()
        self.question_service = QuestionService()
        self.scoring_service = ScoringService()
        self.fsrs_service = FSRSService()
        self.redis_manager = RedisSessionManager()

    async def start_session(self, user_uid: str, topic_id: str) -> Session:
        """Start a new learning session for a topic"""
        
        # Get topic and its questions
        topic = await self.topic_service.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        questions = await self.question_service.get_topic_questions(topic_id)
        if not questions:
            raise ValueError(f"No questions found for topic {topic_id}")
        
        # Create session
        session = Session(
            id=str(uuid.uuid4()),
            userUid=user_uid,
            topicId=topic_id,
            questionIndex=0,
            questionIds=[q.id for q in questions],
            responses=[],
            startedAt=datetime.now()
        )
        
        # Store in both Firebase (persistence) and Redis (fast access)
        await self.repository.create(session)
        await self.redis_manager.store_learning_session(session)
        
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session details - try Redis first, fallback to Firebase"""
        # Try Redis first for speed
        session = await self.redis_manager.get_learning_session(session_id)
        
        if not session:
            # Fallback to Firebase
            session = await self.repository.get_by_id(session_id)
            if session:
                # Store in Redis for future fast access
                await self.redis_manager.store_learning_session(session)
        
        return session

    async def get_current_question(self, session_id: str):
        """Get the current question for a session"""
        session = await self.get_session(session_id)
        if not session:
            return None, None
        
        if session.questionIndex >= len(session.questionIds):
            return session, None  # Session complete
        
        current_question_id = session.questionIds[session.questionIndex]
        question = await self.question_service.get_question(current_question_id)
        
        return session, question

    async def submit_response(self, session_id: str, answer: str) -> dict:
        """Submit response and get feedback with LLM scoring"""
        session, question = await self.get_current_question(session_id)
        
        if not session or not question:
            raise ValueError("Invalid session or question not found")
        
        # Use LLM-powered scoring
        scoring_result = await self.scoring_service.score_response(question, answer)
        
        # Create response record with enhanced feedback
        response = Response(
            questionId=question.id,
            answer=answer,
            score=scoring_result["score"],
            timestamp=datetime.now()
        )
        
        # Update session
        session.responses.append(response)
        session.questionIndex += 1
        
        # Update both Redis and Firebase
        await self._update_session_storage(session)
        
        # Check if session is complete
        is_complete = session.questionIndex >= len(session.questionIds)
        
        result = {
            "score": scoring_result["score"],
            "feedback": scoring_result["feedback"],
            "explanation": scoring_result.get("explanation", ""),
            "correct": scoring_result["correct"],
            "isComplete": is_complete,
            "questionIndex": session.questionIndex,
            "totalQuestions": len(session.questionIds)
        }
        
        if is_complete:
            # Calculate final topic score and update FSRS
            final_score = await self._calculate_final_score(session)
            result["finalScore"] = final_score
            
            # Use real FSRS calculations
            await self._update_topic_fsrs_advanced(session.topicId, final_score)
            
            # Mark session as complete in Redis
            await self.redis_manager.mark_session_complete(session_id, final_score)
        
        return result

    async def skip_question(self, session_id: str) -> dict:
        """Skip current question (score as 0 with feedback)"""
        session, question = await self.get_current_question(session_id)
        
        if not session or not question:
            raise ValueError("Invalid session or question not found")
        
        # Create response for skipped question
        response = Response(
            questionId=question.id,
            answer="",
            score=0,
            timestamp=datetime.now()
        )
        
        session.responses.append(response)
        session.questionIndex += 1
        
        await self._update_session_storage(session)
        
        is_complete = session.questionIndex >= len(session.questionIds)
        
        result = {
            "score": 0,
            "feedback": "Question skipped",
            "explanation": "No response provided",
            "correct": False,
            "isComplete": is_complete,
            "questionIndex": session.questionIndex,
            "totalQuestions": len(session.questionIds)
        }
        
        if is_complete:
            final_score = await self._calculate_final_score(session)
            result["finalScore"] = final_score
            await self._update_topic_fsrs_advanced(session.topicId, final_score)
            await self.redis_manager.mark_session_complete(session_id, final_score)
        
        return result

    async def end_session(self, session_id: str) -> dict:
        """End session early and calculate scores"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        final_score = await self._calculate_final_score(session)
        await self._update_topic_fsrs_advanced(session.topicId, final_score)
        await self.redis_manager.mark_session_complete(session_id, final_score)
        
        return {
            "finalScore": final_score,
            "questionsAnswered": len(session.responses),
            "totalQuestions": len(session.questionIds),
            "averageScore": final_score,
            "sessionDuration": self._calculate_session_duration(session)
        }

    async def _update_session_storage(self, session: Session) -> None:
        """Update session in both Redis and Firebase"""
        try:
            # Update Redis for fast access
            await self.redis_manager.update_session_progress(
                session.id,
                session.questionIndex,
                session.responses
            )
            
            # Update Firebase for persistence
            await self.repository.update(session.id, {
                "responses": [r.dict() for r in session.responses],
                "questionIndex": session.questionIndex
            })
        except Exception as e:
            print(f"Error updating session storage: {e}")

    async def _calculate_final_score(self, session: Session) -> float:
        """Calculate average score for the session"""
        if not session.responses:
            return 0.0
        
        total_score = sum(r.score for r in session.responses)
        return total_score / len(session.responses)

    async def _update_topic_fsrs_advanced(self, topic_id: str, score: float) -> None:
        """Update topic FSRS parameters using real FSRS calculations"""
        try:
            # Get current topic with FSRS params
            topic = await self.topic_service.get_topic(topic_id)
            if not topic:
                return
            
            # Use FSRS service for proper calculations
            performance_score = int(score)  # Convert to 0-5 scale
            fsrs_result = self.fsrs_service.calculate_next_review(
                topic.fsrsParams,
                performance_score,
                datetime.now()
            )
            
            # Update topic with new FSRS parameters
            await self.topic_service.repository.update(topic_id, {
                "fsrsParams": fsrs_result["updatedParams"].dict(),
                "nextReviewAt": fsrs_result["nextReviewAt"].isoformat()
            })
            
            # Invalidate topic cache since we updated it
            self.topic_service.cache.invalidate_user(topic.ownerUid)
            
        except Exception as e:
            print(f"Error updating FSRS parameters: {e}")

    def _calculate_session_duration(self, session: Session) -> int:
        """Calculate session duration in seconds"""
        if session.responses:
            last_response = max(session.responses, key=lambda r: r.timestamp)
            duration = (last_response.timestamp - session.startedAt).total_seconds()
            return int(duration)
        return 0

    # New advanced features for Phase 3

    async def get_session_analytics(self, session_id: str) -> dict:
        """Get detailed analytics for a session"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        total_responses = len(session.responses)
        if total_responses == 0:
            return {"error": "No responses yet"}
        
        scores = [r.score for r in session.responses]
        
        return {
            "totalQuestions": len(session.questionIds),
            "questionsAnswered": total_responses,
            "averageScore": sum(scores) / len(scores),
            "highestScore": max(scores),
            "lowestScore": min(scores),
            "correctAnswers": len([s for s in scores if s >= 3]),
            "sessionDuration": self._calculate_session_duration(session),
            "progressPercentage": (total_responses / len(session.questionIds)) * 100
        }

    async def get_user_session_history(self, user_uid: str) -> list:
        """Get session history for a user from both Redis and Firebase"""
        # Get active sessions from Redis
        redis_sessions = await self.redis_manager.list_user_sessions(user_uid)
        
        # Get completed sessions from Firebase
        firebase_sessions = await self.repository.list_by_user(user_uid)
        
        # Combine and deduplicate
        all_sessions = {}
        
        for session_data in redis_sessions:
            all_sessions[session_data['sessionId']] = session_data['data']
        
        for session in firebase_sessions:
            if session.id not in all_sessions:
                all_sessions[session.id] = session.dict()
        
        return list(all_sessions.values()) 