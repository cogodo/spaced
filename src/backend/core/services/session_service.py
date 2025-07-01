import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.models import FSRSParams, Message, Session
from core.repositories import SessionRepository
from core.services.fsrs_service import FSRSService
from core.services.question_service import QuestionService
from core.services.scoring_service import ScoringService
from core.services.topic_service import TopicService
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
        """Recursively convert Firestore Timestamp objects to native datetimes"""
        # Check if startedAt is a Firestore timestamp and convert it
        if hasattr(session.startedAt, "to_datetime"):
            session.startedAt = session.startedAt.to_datetime()
        elif hasattr(session.startedAt, "ToDatetime"):
            session.startedAt = session.startedAt.ToDatetime()

        # Convert response timestamps (for backward compatibility with old sessions)
        if hasattr(session, "responses") and session.responses:
            for response in session.responses:
                if hasattr(response.timestamp, "to_datetime"):
                    response.timestamp = response.timestamp.to_datetime()
                elif hasattr(response.timestamp, "ToDatetime"):
                    response.timestamp = response.timestamp.ToDatetime()

    def _ensure_session_fields(self, session: Session) -> None:
        """Ensure session has all required fields for backward compatibility"""
        # Add new fields if they don't exist (for old sessions)
        if (
            not hasattr(session, "answeredQuestionIds")
            or session.answeredQuestionIds is None
        ):
            session.answeredQuestionIds = []

        if (
            not hasattr(session, "currentSessionQuestionCount")
            or session.currentSessionQuestionCount is None
        ):
            session.currentSessionQuestionCount = 0

        if (
            not hasattr(session, "maxQuestionsPerSession")
            or session.maxQuestionsPerSession is None
        ):
            session.maxQuestionsPerSession = 5

    async def start_session(
        self, user_uid: str, topic_id: str, session_id: str = None
    ) -> Session:
        """Start a new learning session for a topic"""

        # Use provided session_id or generate new one
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Get topic and its questions
        topic = await self.topic_service.get_topic(topic_id, user_uid)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        questions = await self.question_service.get_topic_questions(topic_id, user_uid)
        if not questions:
            raise ValueError(f"No questions found for topic {topic_id}")

        # Check for existing session to continue progress
        existing_sessions = await self.repository.list_by_user_and_topic(
            user_uid, topic_id
        )

        if existing_sessions:
            # Continue from existing session but use the provided session_id
            existing_session = existing_sessions[0]  # Get most recent

            # Update the session ID to match what frontend expects
            existing_session.id = session_id

            # Ensure backward compatibility
            self._ensure_session_fields(existing_session)

            # Reset current session counter for new session
            existing_session.currentSessionQuestionCount = 0
            existing_session.startedAt = datetime.now()

            # Create/update with the new session ID
            await self.repository.create(existing_session)
            await self.redis_manager.store_learning_session(existing_session)

            return existing_session
        else:
            # Create new session with specified ID
            session = Session(
                id=session_id,  # Use the provided session ID
                userUid=user_uid,
                topicId=topic_id,
                questionIndex=0,
                questionIds=[q.id for q in questions],
                responses=[],
                startedAt=datetime.now(),
                answeredQuestionIds=[],
                currentSessionQuestionCount=0,
                maxQuestionsPerSession=5,
            )

            # Store in both Firebase (persistence) and Redis (fast access)
            await self.repository.create(session)
            print(f"DEBUG: SessionService created session {session.id} in Firebase")

            # Update with topic name for frontend compatibility
            await self.repository.update(
                session.id,
                user_uid,
                {
                    "topics": [topic.name],  # Add topic name for frontend
                    "updatedAt": session.startedAt,
                },
            )
            # Firestore Timestamps are not JSON serializable by default
            self._normalize_firestore_timestamps(session)
            print(f"DEBUG: SessionService updated session {session.id} with topic name")

            # Store in Redis (the existing store_learning_session method handles
            # serialization)
            await self.redis_manager.store_learning_session(session)

            return session

    async def get_session(self, session_id: str, user_uid: str) -> Optional[Session]:
        """Get session details from user's subcollection"""
        # Try Redis first for speed (keeping existing caching)
        session = await self.redis_manager.get_learning_session(session_id)

        if not session:
            # Fallback to DB if not in cache or Redis fails
            session = await self.repository.get_by_id(session_id, user_uid)
            if session:
                # Convert Firestore timestamps to native datetime before storing in
                # Redis
                self._normalize_firestore_timestamps(session)
                # Ensure backward compatibility with old sessions
                self._ensure_session_fields(session)
                # Store in Redis (existing method handles serialization)
                await self.redis_manager.store_learning_session(session)

        if session:
            # Ensure all sessions have the new fields for backward compatibility
            self._ensure_session_fields(session)

        return session

    async def get_session_messages(
        self, session_id: str, user_uid: str
    ) -> List[Message]:
        """Get messages for a session from subcollection"""
        return await self.repository.get_session_messages(user_uid, session_id)

    async def get_current_question(self, session_id: str, user_uid: str):
        """Get the current question for a session (max 5 questions per session)"""
        session = await self.get_session(session_id, user_uid)
        if not session:
            return None, None

        # Check if current session is complete (5 questions answered/skipped)
        if session.currentSessionQuestionCount >= session.maxQuestionsPerSession:
            return session, None  # Current session complete

        # Find next unanswered question
        unanswered_questions = [
            q_id
            for q_id in session.questionIds
            if q_id not in session.answeredQuestionIds
        ]

        if not unanswered_questions:
            return session, None  # All questions in topic bank have been answered

        # Get the next unanswered question
        current_question_id = unanswered_questions[0]
        question = await self.question_service.get_question(
            current_question_id, user_uid, session.topicId
        )

        return session, question

    async def submit_response(
        self, session_id: str, user_uid: str, answer: str
    ) -> dict:
        """Submit response and get feedback with LLM scoring"""
        session, question = await self.get_current_question(session_id, user_uid)

        if not session or not question:
            raise ValueError("Invalid session or question not found")

        # Use LLM-powered scoring
        scoring_result = await self.scoring_service.score_response(question, answer)

        # Add message to subcollection (with embedded question text for efficiency)
        await self.repository.add_message(
            user_uid=user_uid,
            session_id=session_id,
            question_id=question.id,
            question_text=question.text,
            answer_text=answer,
            score=scoring_result["score"],
        )

        # Update session - track answered questions and current session progress
        session.answeredQuestionIds.append(question.id)
        session.currentSessionQuestionCount += 1

        # Update session metadata in Firebase
        await self.repository.update(
            session_id,
            user_uid,
            {
                "answeredQuestionIds": session.answeredQuestionIds,
                "currentSessionQuestionCount": session.currentSessionQuestionCount,
                "messageCount": len(
                    session.answeredQuestionIds
                ),  # Update message count
                "updatedAt": datetime.now(),
                "lastMessageAt": datetime.now(),
            },
        )

        # Update Redis cache
        await self.redis_manager.store_learning_session(session)

        # Check if current session is complete (5 questions) or all questions answered
        current_session_complete = (
            session.currentSessionQuestionCount >= session.maxQuestionsPerSession
        )
        all_questions_answered = len(session.answeredQuestionIds) >= len(
            session.questionIds
        )

        result = {
            "score": scoring_result["score"],
            "feedback": scoring_result["feedback"],
            "explanation": scoring_result.get("explanation", ""),
            "correct": scoring_result["correct"],
            "isComplete": current_session_complete,
            "questionIndex": session.currentSessionQuestionCount,
            "totalQuestions": session.maxQuestionsPerSession,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds),
        }

        if current_session_complete:
            # Get current session messages for scoring
            messages = await self.get_session_messages(session_id, user_uid)
            current_session_messages = (
                messages[-session.currentSessionQuestionCount :]
                if len(messages) >= session.currentSessionQuestionCount
                else messages
            )
            session_score = await self._calculate_session_score_from_messages(
                current_session_messages
            )
            result["finalScore"] = session_score

            # Update FSRS after each session completion using session performance
            fsrs_update = await self._update_topic_fsrs_advanced(
                session.topicId, session_score, user_uid
            )
            result["fsrs"] = fsrs_update

            # Check if all topic questions are answered for completion status
            if all_questions_answered:
                overall_score = await self._calculate_final_score_from_messages(
                    messages
                )
                result["topicComplete"] = True
                result["overallTopicScore"] = overall_score

            # Mark session as complete in both Redis and Firebase
            await self.redis_manager.mark_session_complete(session_id, session_score)
            await self.repository.update(
                session_id,
                user_uid,
                {
                    "isCompleted": True,
                    "state": "completed",
                    "finalScores": {"overall": int(session_score * 20)},
                    "updatedAt": datetime.now(),
                },
            )

        return result

    async def skip_question(self, session_id: str, user_uid: str) -> dict:
        """Skip current question (score as 0 with feedback)"""
        session, question = await self.get_current_question(session_id, user_uid)

        if not session or not question:
            raise ValueError("Invalid session or question not found")

        # Add skipped message to subcollection (with embedded question text for
        # efficiency)
        await self.repository.add_message(
            user_uid=user_uid,
            session_id=session_id,
            question_id=question.id,
            question_text=question.text,
            answer_text="",  # Empty for skipped
            score=0,
        )

        # Update session - track answered questions and current session progress
        session.answeredQuestionIds.append(question.id)
        session.currentSessionQuestionCount += 1

        # Update session metadata in Firebase
        await self.repository.update(
            session_id,
            user_uid,
            {
                "answeredQuestionIds": session.answeredQuestionIds,
                "currentSessionQuestionCount": session.currentSessionQuestionCount,
                "messageCount": len(
                    session.answeredQuestionIds
                ),  # Update message count
                "updatedAt": datetime.now(),
                "lastMessageAt": datetime.now(),
            },
        )

        # Update Redis cache
        await self.redis_manager.store_learning_session(session)

        # Check if current session is complete (5 questions) or all questions answered
        current_session_complete = (
            session.currentSessionQuestionCount >= session.maxQuestionsPerSession
        )
        all_questions_answered = len(session.answeredQuestionIds) >= len(
            session.questionIds
        )

        result = {
            "score": 0,
            "feedback": "Question skipped",
            "explanation": "No response provided",
            "correct": False,
            "isComplete": current_session_complete,
            "questionIndex": session.currentSessionQuestionCount,
            "totalQuestions": session.maxQuestionsPerSession,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds),
        }

        if current_session_complete:
            # Get current session messages for scoring
            messages = await self.get_session_messages(session_id, user_uid)
            current_session_messages = (
                messages[-session.currentSessionQuestionCount :]
                if len(messages) >= session.currentSessionQuestionCount
                else messages
            )
            session_score = await self._calculate_session_score_from_messages(
                current_session_messages
            )
            result["finalScore"] = session_score

            # Update FSRS after each session completion using session performance
            fsrs_update = await self._update_topic_fsrs_advanced(
                session.topicId, session_score, user_uid
            )
            result["fsrs"] = fsrs_update

            # Check if all topic questions are answered for completion status
            if all_questions_answered:
                overall_score = await self._calculate_final_score_from_messages(
                    messages
                )
                result["topicComplete"] = True
                result["overallTopicScore"] = overall_score

            await self.redis_manager.mark_session_complete(session_id, session_score)
            await self.repository.update(
                session_id,
                user_uid,
                {
                    "isCompleted": True,
                    "state": "completed",
                    "finalScores": {"overall": int(session_score * 20)},
                    "updatedAt": datetime.now(),
                },
            )
        else:
            # Get the next question if session is not complete
            _, next_question = await self.get_current_question(session_id, user_uid)
            if next_question:
                result["nextQuestion"] = next_question.text

        return result

    async def end_session(self, session_id: str, user_uid: str) -> dict:
        """End session early and calculate scores for current session only"""
        session = await self.get_session(session_id, user_uid)
        if not session:
            raise ValueError("Session not found")

        # Ensure backward compatibility
        self._ensure_session_fields(session)

        # Get session messages for scoring with error handling
        try:
            messages = await self.get_session_messages(session_id, user_uid)
        except Exception as e:
            print(f"Warning: Could not retrieve session messages: {e}")
            messages = []

        # Calculate score for current session messages only
        if session.currentSessionQuestionCount > 0 and messages:
            # Filter only actual answered messages (not empty or placeholder messages)
            valid_messages = [
                m
                for m in messages
                if m.answerText and m.answerText.strip() and m.score > 0
            ]
            current_session_messages = (
                valid_messages[-session.currentSessionQuestionCount :]
                if len(valid_messages) >= session.currentSessionQuestionCount
                else valid_messages
            )

            if current_session_messages:
                session_score = await self._calculate_session_score_from_messages(
                    current_session_messages
                )
                questions_answered = len(current_session_messages)
            else:
                session_score = 0.0
                questions_answered = 0

            # Update FSRS after session end using session performance
            try:
                fsrs_update = await self._update_topic_fsrs_advanced(
                    session.topicId, session_score, user_uid
                )
            except Exception as e:
                print(f"Warning: Could not update FSRS parameters: {e}")
                fsrs_update = {}
        else:
            session_score = 0.0
            questions_answered = 0
            fsrs_update = {}

        # Mark session as complete in Redis
        try:
            await self.redis_manager.mark_session_complete(session_id, session_score)
        except Exception as e:
            print(f"Warning: Could not mark session complete in Redis: {e}")

        # Update session state in Firebase
        try:
            await self.repository.update(
                session_id,
                user_uid,
                {
                    "isCompleted": True,
                    "state": "completed",
                    "finalScores": {"overall": int(session_score * 20)}
                    if session_score > 0
                    else {"overall": 0},
                    "updatedAt": datetime.now(),
                },
            )
        except Exception as e:
            print(f"Warning: Could not update session state in Firebase: {e}")

        result = {
            "finalScore": session_score,
            "questionsAnswered": questions_answered,
            "totalQuestions": session.currentSessionQuestionCount,
            "averageScore": session_score,
            "sessionDuration": self._calculate_session_duration_from_messages(messages)
            if messages
            else 0,
            "isComplete": True,
            "questionIndex": session.currentSessionQuestionCount,
            "topicProgress": len(session.answeredQuestionIds),
            "totalTopicQuestions": len(session.questionIds),
        }

        # Add FSRS update info to response if available
        if fsrs_update:
            result["fsrs"] = fsrs_update

        return result

    async def _calculate_session_score_from_messages(
        self, messages: List[Message]
    ) -> float:
        """Calculate average score for a specific set of messages"""
        if not messages:
            return 0.0

        total_score = sum(m.score for m in messages)
        return total_score / len(messages)

    async def _calculate_final_score_from_messages(
        self, messages: List[Message]
    ) -> float:
        """Calculate average score for all messages in the session"""
        if not messages:
            return 0.0

        total_score = sum(m.score for m in messages)
        return total_score / len(messages)

    async def _update_topic_fsrs_advanced(
        self, topic_id: str, score: float, user_uid: str
    ) -> Dict[str, Any]:
        """
        Update topic FSRS parameters using real FSRS calculations and return
        review info
        """
        try:
            print(
                f"FSRS UPDATE: Starting update for topic {topic_id}, score {score}, "
                f"user {user_uid}"
            )
            # Get the topic from the database
            topic = await self.topic_service.get_topic(topic_id, user_uid)
            if not topic:
                print(f"FSRS UPDATE: Topic {topic_id} not found, skipping update")
                return {}

            # Ensure fsrsParams is initialized
            if not topic.fsrsParams:
                topic.fsrsParams = FSRSParams()  # Initialize with defaults

            print(
                f"FSRS UPDATE: Current params - ease: {topic.fsrsParams.ease}, "
                f"interval: {topic.fsrsParams.interval}, repetition: "
                f"{topic.fsrsParams.repetition}"
            )

            # Calculate new FSRS parameters based on score
            fsrs_result = self.fsrs_service.calculate_next_review(
                topic.fsrsParams, score
            )
            print(
                f"FSRS UPDATE: New params calculated - interval: "
                f"{fsrs_result['intervalDays']} days"
            )

            # Update topic's FSRS parameters in database
            await self.topic_service.update_fsrs_params(
                topic_id,
                user_uid,
                fsrs_result["newEase"],
                fsrs_result["intervalDays"],
                fsrs_result["repetitionCount"],
            )

            # Get the updated topic to calculate next review date
            updated_topic = await self.topic_service.get_topic(topic_id, user_uid)
            days_until_review = (
                (updated_topic.nextReviewAt - datetime.now()).days
                if updated_topic.nextReviewAt
                else 0
            )

            result = {
                "nextReviewDays": days_until_review,
                "newEase": fsrs_result["newEase"],
            }
            print(
                f"FSRS UPDATE: Successfully updated topic {topic_id}, next review "
                f"in {days_until_review} days"
            )
            return result
        except Exception as e:
            print(
                f"FSRS UPDATE ERROR: Failed to update FSRS parameters for topic "
                f"{topic_id}: {e}"
            )
            return {}

    def _calculate_session_duration(self, session: Session) -> int:
        """Calculate session duration in seconds (legacy method)"""
        return 0  # Legacy method, not used in new structure

    def _calculate_session_duration_from_messages(self, messages: List[Message]) -> int:
        """Calculate session duration from messages"""
        if not messages:
            return 0

        first_message = min(messages, key=lambda m: m.timestamp)
        last_message = max(messages, key=lambda m: m.timestamp)
        duration = (last_message.timestamp - first_message.timestamp).total_seconds()
        return int(duration)

    # New advanced features for Phase 3

    async def get_session_analytics(self, session_id: str, user_uid: str) -> dict:
        """Get detailed analytics for a session"""
        session = await self.get_session(session_id, user_uid)
        if not session:
            return {}

        # Get messages for this session
        messages = await self.get_session_messages(session_id, user_uid)
        total_responses = len(messages)
        if total_responses == 0:
            return {"error": "No responses yet"}

        scores = [m.score for m in messages]

        return {
            "totalQuestions": len(session.questionIds),
            "questionsAnswered": total_responses,
            "averageScore": sum(scores) / len(scores),
            "highestScore": max(scores),
            "lowestScore": min(scores),
            "correctAnswers": len([s for s in scores if s >= 3]),
            "sessionDuration": self._calculate_session_duration_from_messages(messages),
            "progressPercentage": (total_responses / len(session.questionIds)) * 100,
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
            all_sessions[session_data["sessionId"]] = session_data["data"]

        for session in firebase_sessions:
            if session.id not in all_sessions:
                all_sessions[session.id] = session.dict()

        return list(all_sessions.values())
