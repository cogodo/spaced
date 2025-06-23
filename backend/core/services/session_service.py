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

    def _normalize_firestore_timestamps(self, session: Session) -> None:
        """Convert Firestore DatetimeWithNanoseconds to native datetime objects"""
        # Check if startedAt is a Firestore timestamp and convert it
        if hasattr(session.startedAt, 'to_datetime'):
            session.startedAt = session.startedAt.to_datetime()
        elif hasattr(session.startedAt, 'ToDatetime'):
            session.startedAt = session.startedAt.ToDatetime()
        
        # Convert response timestamps
        for response in session.responses:
            if hasattr(response.timestamp, 'to_datetime'):
                response.timestamp = response.timestamp.to_datetime()
            elif hasattr(response.timestamp, 'ToDatetime'):
                response.timestamp = response.timestamp.ToDatetime()
    
    def _ensure_session_fields(self, session: Session) -> None:
        """Ensure session has all required fields for backward compatibility"""
        # Add new fields if they don't exist (for old sessions)
        if not hasattr(session, 'answeredQuestionIds') or session.answeredQuestionIds is None:
            session.answeredQuestionIds = []
        
        if not hasattr(session, 'currentSessionQuestionCount') or session.currentSessionQuestionCount is None:
            session.currentSessionQuestionCount = 0
        
        if not hasattr(session, 'maxQuestionsPerSession') or session.maxQuestionsPerSession is None:
            session.maxQuestionsPerSession = 5

    async def start_session(self, user_uid: str, topic_id: str) -> Session:
        """Start a new learning session for a topic"""
        
        # Get topic and its questions
        topic = await self.topic_service.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        questions = await self.question_service.get_topic_questions(topic_id)
        if not questions:
            raise ValueError(f"No questions found for topic {topic_id}")
        
        # Check for existing session to continue progress
        existing_sessions = await self.repository.list_by_user_and_topic(user_uid, topic_id)
        
        if existing_sessions:
            # Continue from existing session
            existing_session = existing_sessions[0]  # Get most recent
            
            # Ensure backward compatibility
            self._ensure_session_fields(existing_session)
            
            # Reset current session counter for new session
            existing_session.currentSessionQuestionCount = 0
            existing_session.startedAt = datetime.now()
            
            # Update both Firebase and Redis
            await self.repository.update(existing_session.id, {
                "currentSessionQuestionCount": 0,
                "startedAt": existing_session.startedAt,
                "answeredQuestionIds": existing_session.answeredQuestionIds,
                "maxQuestionsPerSession": existing_session.maxQuestionsPerSession
            })
            await self.redis_manager.store_learning_session(existing_session)
            
            return existing_session
        else:
            # Create new session
            session = Session(
                id=str(uuid.uuid4()),
                userUid=user_uid,
                topicId=topic_id,
                questionIndex=0,
                questionIds=[q.id for q in questions],
                responses=[],
                startedAt=datetime.now(),
                answeredQuestionIds=[],
                currentSessionQuestionCount=0,
                maxQuestionsPerSession=5
            )
            
            # Store in both Firebase (persistence) and Redis (fast access)
            await self.repository.create(session)
            # Store in Redis (the existing store_learning_session method handles serialization)
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
                # Convert Firestore timestamps to native datetime before storing in Redis
                self._normalize_firestore_timestamps(session)
                # Ensure backward compatibility with old sessions
                self._ensure_session_fields(session)
                # Store in Redis (existing method handles serialization)
                await self.redis_manager.store_learning_session(session)
        
        if session:
            # Ensure all sessions have the new fields for backward compatibility
            self._ensure_session_fields(session)
        
        return session

    async def get_current_question(self, session_id: str):
        """Get the current question for a session (max 5 questions per session)"""
        session = await self.get_session(session_id)
        if not session:
            return None, None
        
        # Check if current session is complete (5 questions answered/skipped)
        if session.currentSessionQuestionCount >= session.maxQuestionsPerSession:
            return session, None  # Current session complete
        
        # Find next unanswered question
        unanswered_questions = [q_id for q_id in session.questionIds if q_id not in session.answeredQuestionIds]
        
        if not unanswered_questions:
            return session, None  # All questions in topic bank have been answered
        
        # Get the next unanswered question
        current_question_id = unanswered_questions[0]
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
        
        # Update session - track answered questions and current session progress
        session.responses.append(response)
        session.answeredQuestionIds.append(question.id)
        session.currentSessionQuestionCount += 1
        
        # Update both Redis and Firebase
        await self._update_session_storage(session)
        
        # Check if current session is complete (5 questions) or all questions answered
        current_session_complete = session.currentSessionQuestionCount >= session.maxQuestionsPerSession
        all_questions_answered = len(session.answeredQuestionIds) >= len(session.questionIds)
        
        result = {
            "score": scoring_result["score"],
            "feedback": scoring_result["feedback"],
            "explanation": scoring_result.get("explanation", ""),
            "correct": scoring_result["correct"],
            "isComplete": current_session_complete,
            "questionIndex": session.currentSessionQuestionCount,
            "totalQuestions": session.maxQuestionsPerSession,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds)
        }
        
        if current_session_complete:
            # Calculate session score (for this set of 5 questions)
            # Ensure we don't try to slice beyond the list length
            responses_count = min(session.currentSessionQuestionCount, len(session.responses))
            current_session_responses = session.responses[-responses_count:] if responses_count > 0 else []
            session_score = await self._calculate_session_score(current_session_responses)
            result["finalScore"] = session_score
            
            # If all topic questions are answered, update FSRS with overall performance
            if all_questions_answered:
                overall_score = await self._calculate_final_score(session)
                await self._update_topic_fsrs_advanced(session.topicId, overall_score)
                result["topicComplete"] = True
                result["overallTopicScore"] = overall_score
            
            # Mark session as complete in Redis
            await self.redis_manager.mark_session_complete(session_id, session_score)
        
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
        
        # Update session - track answered questions and current session progress
        session.responses.append(response)
        session.answeredQuestionIds.append(question.id)
        session.currentSessionQuestionCount += 1
        
        await self._update_session_storage(session)
        
        # Check if current session is complete (5 questions) or all questions answered
        current_session_complete = session.currentSessionQuestionCount >= session.maxQuestionsPerSession
        all_questions_answered = len(session.answeredQuestionIds) >= len(session.questionIds)
        
        result = {
            "score": 0,
            "feedback": "Question skipped",
            "explanation": "No response provided",
            "correct": False,
            "isComplete": current_session_complete,
            "questionIndex": session.currentSessionQuestionCount,
            "totalQuestions": session.maxQuestionsPerSession,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds)
        }
        
        if current_session_complete:
            # Calculate session score (for this set of 5 questions)
            # Ensure we don't try to slice beyond the list length
            responses_count = min(session.currentSessionQuestionCount, len(session.responses))
            current_session_responses = session.responses[-responses_count:] if responses_count > 0 else []
            session_score = await self._calculate_session_score(current_session_responses)
            result["finalScore"] = session_score
            
            # If all topic questions are answered, update FSRS with overall performance
            if all_questions_answered:
                overall_score = await self._calculate_final_score(session)
                await self._update_topic_fsrs_advanced(session.topicId, overall_score)
                result["topicComplete"] = True
                result["overallTopicScore"] = overall_score
            
            await self.redis_manager.mark_session_complete(session_id, session_score)
        else:
            # Get the next question if session is not complete
            _, next_question = await self.get_current_question(session_id)
            if next_question:
                result["nextQuestion"] = next_question.text
        
        return result

    async def end_session(self, session_id: str) -> dict:
        """End session early and calculate scores for current session only"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Ensure backward compatibility
        self._ensure_session_fields(session)
        
        # Calculate score for current session responses only
        if session.currentSessionQuestionCount > 0:
            responses_count = min(session.currentSessionQuestionCount, len(session.responses))
            current_session_responses = session.responses[-responses_count:] if responses_count > 0 else []
            session_score = await self._calculate_session_score(current_session_responses)
        else:
            session_score = 0.0
        
        # Mark session as complete in Redis
        await self.redis_manager.mark_session_complete(session_id, session_score)
        
        # Calculate actual answered questions for current session (excluding skipped ones)
        if session.currentSessionQuestionCount > 0:
            responses_count = min(session.currentSessionQuestionCount, len(session.responses))
            current_session_responses = session.responses[-responses_count:] if responses_count > 0 else []
            questions_answered = len([r for r in current_session_responses if r.answer.strip() != ""])
        else:
            questions_answered = 0
        
        return {
            "finalScore": session_score,
            "questionsAnswered": questions_answered,
            "totalQuestions": session.currentSessionQuestionCount,
            "averageScore": session_score,
            "sessionDuration": self._calculate_session_duration(session),
            "isComplete": True,
            "questionIndex": session.currentSessionQuestionCount,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds)
        }

    async def _update_session_storage(self, session: Session) -> None:
        """Update session in both Redis and Firebase"""
        try:
            # Normalize any Firestore timestamps first
            self._normalize_firestore_timestamps(session)
            
            # Prepare responses for Redis - convert timestamps to ensure JSON serialization
            responses_for_redis = []
            for response in session.responses:
                response_dict = response.dict()
                # Ensure timestamp is native datetime before Redis serialization
                if hasattr(response.timestamp, 'to_datetime'):
                    response.timestamp = response.timestamp.to_datetime()
                elif hasattr(response.timestamp, 'ToDatetime'):
                    response.timestamp = response.timestamp.ToDatetime()
                responses_for_redis.append(response_dict)
            
            # Update Redis using existing method (it handles JSON serialization internally)
            await self.redis_manager.update_session_progress(
                session.id,
                session.questionIndex,
                responses_for_redis
            )
            
            # Update Firebase for persistence
            await self.repository.update(session.id, {
                "responses": [r.dict() for r in session.responses],
                "questionIndex": session.questionIndex,
                "answeredQuestionIds": session.answeredQuestionIds,
                "currentSessionQuestionCount": session.currentSessionQuestionCount
            })
        except Exception as e:
            print(f"Error updating session storage: {e}")

    async def _calculate_final_score(self, session: Session) -> float:
        """Calculate average score for all responses in the session"""
        if not session.responses:
            return 0.0
        
        total_score = sum(r.score for r in session.responses)
        return total_score / len(session.responses)
    
    async def _calculate_session_score(self, responses: List[Response]) -> float:
        """Calculate average score for a specific set of responses"""
        if not responses:
            return 0.0
        
        total_score = sum(r.score for r in responses)
        return total_score / len(responses)

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