import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """FSRS Task data structure matching the Firebase schema"""
    task_name: str
    difficulty: float
    last_review_date: str
    next_review_date: str
    previous_interval: int
    repetition: int
    stability: float
    days_since_init: int
    
    @property
    def is_due(self) -> bool:
        """Check if task is due for review (nextReviewDate <= today)"""
        try:
            next_review = datetime.fromisoformat(self.next_review_date.replace('Z', '+00:00'))
            today = datetime.now(timezone.utc)
            return next_review.date() <= today.date()
        except Exception as e:
            logger.error(f"Error checking due date for task {self.task_name}: {e}")
            return False
    
    @property
    def days_overdue(self) -> int:
        """Calculate how many days overdue this task is (0 if not overdue)"""
        try:
            next_review = datetime.fromisoformat(self.next_review_date.replace('Z', '+00:00'))
            today = datetime.now(timezone.utc)
            days_diff = (today.date() - next_review.date()).days
            return max(0, days_diff)
        except Exception:
            return 0

@dataclass
class SessionMetrics:
    """Comprehensive session performance metrics"""
    session_id: str
    user_id: str
    session_type: str  # "due_items" or "custom_topics"
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    
    # Topic/Task metrics
    topics_covered: List[str]
    total_questions: int
    questions_per_topic: Dict[str, int]
    
    # Question type analytics
    question_types_used: List[str]
    question_type_distribution: Dict[str, int]
    
    # Performance metrics
    scores: Dict[str, int]  # topic -> score (0-5)
    average_score: float
    score_variance: float
    
    # FSRS-specific metrics (for due_items sessions)
    initial_difficulties: Optional[Dict[str, float]] = None
    avg_initial_difficulty: Optional[float] = None
    overdue_items_count: Optional[int] = None
    total_overdue_days: Optional[int] = None
    
    # Learning analytics
    answer_quality_metrics: Optional[Dict[str, Dict[str, float]]] = None
    difficulty_adaptation_stats: Optional[Dict[str, Any]] = None

@dataclass  
class LearningInsights:
    """User learning performance insights"""
    user_id: str
    analysis_period_days: int
    
    # Session statistics
    total_sessions: int
    due_items_sessions: int
    custom_topics_sessions: int
    total_study_time_minutes: int
    avg_session_duration_minutes: float
    
    # Performance trends
    average_scores: Dict[str, float]  # topic -> avg score
    score_trends: Dict[str, List[float]]  # topic -> [scores over time]
    improvement_rate: Dict[str, float]  # topic -> score improvement per session
    
    # Recommendations
    struggling_topics: List[str]  # Topics with low scores
    mastered_topics: List[str]    # Topics with high scores
    recommended_review_frequency: Dict[str, int]  # topic -> days between reviews
    
    # FSRS effectiveness (optional fields)
    fsrs_accuracy: Optional[float] = None  # How often FSRS predictions were accurate
    difficulty_adaptation_success: Optional[float] = None


class FirebaseService:
    """Enhanced Firebase service with comprehensive FSRS integration and analytics"""
    
    def __init__(self):
        self._db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Priority 1: Local service account file (for development)
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', './firebase-service-account.json')
                if os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase initialized with service account file: {service_account_path}")
                
                # Priority 2: Environment variable with service account JSON (for production)
                elif os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'):
                    service_account_info = json.loads(os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON'))
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized with service account JSON from environment")
                
                # Priority 3: Application Default Credentials (fallback)
                else:
                    firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            
            self._db = firestore.client()
            logger.info("Firebase Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            logger.error("Make sure you have:")
            logger.error("1. firebase-service-account.json file in backend/ directory, OR")
            logger.error("2. FIREBASE_SERVICE_ACCOUNT_JSON environment variable set, OR") 
            logger.error("3. Application Default Credentials configured")
            raise
    
    async def verify_user_token(self, id_token: str) -> str:
        """Verify Firebase ID token and return user ID"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            logger.info(f"Token verified for user: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {e}")
    
    async def get_all_tasks(self, user_id: str) -> List[Task]:
        """Fetch all tasks for a user from users/{userId}/tasks/{taskName}"""
        try:
            tasks_ref = self._db.collection('users').document(user_id).collection('tasks')
            docs = tasks_ref.stream()
            
            tasks = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    task = Task(
                        task_name=data.get('task', doc.id),  # Use doc.id as fallback
                        difficulty=data.get('difficulty', 0.5),
                        last_review_date=data.get('lastReviewDate', ''),
                        next_review_date=data.get('nextReviewDate', ''),
                        previous_interval=data.get('previousInterval', 0),
                        repetition=data.get('repetition', 0),
                        stability=data.get('stability', 1.0),
                        days_since_init=data.get('daysSinceInit', 0)
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error parsing task {doc.id}: {e}")
                    continue
            
            logger.info(f"Fetched {len(tasks)} tasks for user {user_id}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks for user {user_id}: {e}")
            raise
    
    async def get_due_tasks(self, user_id: str) -> List[Task]:
        """Get tasks that are due for review"""
        all_tasks = await self.get_all_tasks(user_id)
        due_tasks = [task for task in all_tasks if task.is_due]
        logger.info(f"Found {len(due_tasks)} due tasks for user {user_id}")
        return due_tasks
    
    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Prioritize tasks for review session.
        Priority: highest difficulty first, then most overdue
        """
        def priority_key(task: Task) -> tuple:
            # Higher difficulty = higher priority (sort descending)
            # More overdue days = higher priority (sort descending)
            return (-task.difficulty, -task.days_overdue, task.task_name)
        
        prioritized = sorted(tasks, key=priority_key)
        logger.info(f"Prioritized {len(prioritized)} tasks by difficulty and overdue status")
        return prioritized
    
    async def update_task_after_review(self, user_id: str, task_name: str, score: int, 
                                     session_data: Optional[Dict] = None) -> bool:
        """
        Enhanced task update with comprehensive session metadata
        """
        try:
            task_ref = self._db.collection('users').document(user_id).collection('tasks').document(task_name)
            
            # Enhanced update data
            update_data = {
                'lastChatReview': firestore.SERVER_TIMESTAMP,
                'lastChatScore': score,
                'chatReviewCount': firestore.Increment(1)
            }
            
            # Add session-specific metadata if provided
            if session_data:
                update_data.update({
                    'lastSessionType': session_data.get('session_type'),
                    'lastQuestionTypes': session_data.get('question_types', []),
                    'lastDifficultyAdaptation': session_data.get('difficulty_adaptation'),
                    'lastAnswerQualityMetrics': session_data.get('answer_quality')
                })
            
            task_ref.update(update_data)
            logger.info(f"Enhanced update for task {task_name} with score {score}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task {task_name} for user {user_id}: {e}")
            return False
    
    async def save_session_metrics(self, metrics: SessionMetrics) -> bool:
        """Save comprehensive session analytics to Firebase"""
        try:
            sessions_ref = self._db.collection('users').document(metrics.user_id).collection('session_analytics')
            
            # Convert metrics to dictionary
            metrics_data = asdict(metrics)
            
            # Convert datetime objects to timestamps
            metrics_data['start_time'] = metrics.start_time
            metrics_data['end_time'] = metrics.end_time
            
            # Add the session document
            doc_ref = sessions_ref.add(metrics_data)
            logger.info(f"Session metrics saved with ID: {doc_ref[1].id}")
            
            # Update user-level statistics
            await self._update_user_stats(metrics)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session metrics: {e}")
            return False
    
    async def _update_user_stats(self, metrics: SessionMetrics) -> None:
        """Update aggregated user statistics"""
        try:
            user_stats_ref = self._db.collection('users').document(metrics.user_id).collection('statistics').document('learning_analytics')
            
            # Increment counters and update averages
            update_data = {
                'totalSessions': firestore.Increment(1),
                'totalQuestions': firestore.Increment(metrics.total_questions),
                'totalStudyTimeSeconds': firestore.Increment(metrics.duration_seconds),
                'lastSessionDate': firestore.SERVER_TIMESTAMP,
                'recentAverageScore': metrics.average_score,  # Latest session average
            }
            
            # Session type counters
            if metrics.session_type == 'due_items':
                update_data['dueItemsSessions'] = firestore.Increment(1)
            else:
                update_data['customTopicsSessions'] = firestore.Increment(1)
            
            user_stats_ref.set(update_data, merge=True)
            logger.info(f"Updated user statistics for {metrics.user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user statistics: {e}")
    
    async def get_learning_insights(self, user_id: str, days: int = 30) -> Optional[LearningInsights]:
        """Generate comprehensive learning insights for a user"""
        try:
            # Get recent session data
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            sessions_ref = self._db.collection('users').document(user_id).collection('session_analytics')
            
            query = sessions_ref.where('start_time', '>=', cutoff_date).order_by('start_time')
            sessions_docs = query.stream()
            
            sessions_data = [doc.to_dict() for doc in sessions_docs]
            
            if not sessions_data:
                logger.info(f"No sessions found for user {user_id} in the last {days} days")
                return None
            
            # Analyze sessions and generate insights
            insights = self._analyze_sessions(user_id, sessions_data, days)
            logger.info(f"Generated learning insights for user {user_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights for user {user_id}: {e}")
            return None
    
    def _analyze_sessions(self, user_id: str, sessions_data: List[Dict], days: int) -> LearningInsights:
        """Analyze session data to generate insights"""
        
        # Basic session statistics
        total_sessions = len(sessions_data)
        due_items_sessions = sum(1 for s in sessions_data if s.get('session_type') == 'due_items')
        custom_topics_sessions = total_sessions - due_items_sessions
        
        total_study_time = sum(s.get('duration_seconds', 0) for s in sessions_data)
        avg_session_duration = total_study_time / total_sessions if total_sessions > 0 else 0
        
        # Performance analysis
        all_scores = {}
        score_trends = {}
        
        for session in sessions_data:
            scores = session.get('scores', {})
            for topic, score in scores.items():
                if topic not in all_scores:
                    all_scores[topic] = []
                    score_trends[topic] = []
                all_scores[topic].append(score)
                score_trends[topic].append(score)
        
        # Calculate averages and improvements
        average_scores = {topic: sum(scores) / len(scores) for topic, scores in all_scores.items()}
        improvement_rate = {}
        
        for topic, scores in score_trends.items():
            if len(scores) >= 2:
                # Simple linear improvement calculation
                improvement = (scores[-1] - scores[0]) / len(scores)
                improvement_rate[topic] = improvement
            else:
                improvement_rate[topic] = 0.0
        
        # Identify struggling and mastered topics
        struggling_topics = [topic for topic, avg_score in average_scores.items() if avg_score < 2.5]
        mastered_topics = [topic for topic, avg_score in average_scores.items() if avg_score >= 4.0]
        
        # Generate recommendations
        recommended_review_frequency = {}
        for topic, avg_score in average_scores.items():
            if avg_score < 2.0:
                recommended_review_frequency[topic] = 1  # Daily review
            elif avg_score < 3.0:
                recommended_review_frequency[topic] = 3  # Every 3 days
            elif avg_score < 4.0:
                recommended_review_frequency[topic] = 7  # Weekly
            else:
                recommended_review_frequency[topic] = 14  # Bi-weekly
        
        return LearningInsights(
            user_id=user_id,
            analysis_period_days=days,
            total_sessions=total_sessions,
            due_items_sessions=due_items_sessions,
            custom_topics_sessions=custom_topics_sessions,
            total_study_time_minutes=total_study_time // 60,
            avg_session_duration_minutes=avg_session_duration / 60,
            average_scores=average_scores,
            score_trends=score_trends,
            improvement_rate=improvement_rate,
            struggling_topics=struggling_topics,
            mastered_topics=mastered_topics,
            recommended_review_frequency=recommended_review_frequency
        )
    
    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        try:
            # Get current due tasks
            due_tasks = await self.get_due_tasks(user_id)
            
            # Get recent learning insights
            insights = await self.get_learning_insights(user_id, days=7)  # Last week
            monthly_insights = await self.get_learning_insights(user_id, days=30)  # Last month
            
            # Get user statistics
            stats_ref = self._db.collection('users').document(user_id).collection('statistics').document('learning_analytics')
            stats_doc = stats_ref.get()
            user_stats = stats_doc.to_dict() if stats_doc.exists else {}
            
            dashboard_data = {
                'current_status': {
                    'due_tasks_count': len(due_tasks),
                    'overdue_tasks': [t.task_name for t in due_tasks if t.days_overdue > 0],
                    'priority_tasks': [t.task_name for t in due_tasks[:5]],  # Top 5 priority
                },
                'weekly_progress': {
                    'sessions_completed': insights.total_sessions if insights else 0,
                    'total_study_minutes': insights.total_study_time_minutes if insights else 0,
                    'average_score': sum(insights.average_scores.values()) / len(insights.average_scores) if insights and insights.average_scores else 0,
                    'topics_studied': list(insights.average_scores.keys()) if insights else []
                },
                'monthly_trends': {
                    'total_sessions': monthly_insights.total_sessions if monthly_insights else 0,
                    'improvement_rate': monthly_insights.improvement_rate if monthly_insights else {},
                    'struggling_topics': monthly_insights.struggling_topics if monthly_insights else [],
                    'mastered_topics': monthly_insights.mastered_topics if monthly_insights else []
                },
                'recommendations': {
                    'review_frequency': monthly_insights.recommended_review_frequency if monthly_insights else {},
                    'suggested_session_type': 'due_items' if len(due_tasks) > 0 else 'custom_topics',
                    'focus_areas': insights.struggling_topics[:3] if insights else []  # Top 3 struggling topics
                },
                'lifetime_stats': user_stats
            }
            
            logger.info(f"Generated dashboard data for user {user_id}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data for {user_id}: {e}")
            return {}


class QuestionBankService:
    """Service for managing topic question banks in Firebase"""
    
    def __init__(self, firebase_service: FirebaseService = None):
        self.firebase_service = firebase_service or FirebaseService()
        self._db = self.firebase_service._db
    
    async def ensure_topic_has_questions(self, user_id: str, topic_id: str, topic_name: str, topic_context: str = "") -> bool:
        """Ensure topic has question bank, generate if needed"""
        try:
            # Check if topic already has unused questions
            existing_questions = await self.get_unused_questions(user_id, topic_id, limit=1)
            
            if existing_questions:
                logger.info(f"Topic {topic_id} already has questions")
                return True
            
            # Check if topic exists but all questions are used
            topic_ref = (
                self._db
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
                    # Generate new questions
                    from .question_generator import QuestionGenerationService
                    question_service = QuestionGenerationService()
                    questions = await question_service.generate_topic_questions(topic_name, topic_context)
                    
                    if questions:
                        success = await question_service.store_questions_in_firebase(user_id, topic_id, questions)
                        return success
                    return False
                else:
                    logger.info(f"Topic {topic_id} has questions available")
                    return True
            
            # Generate questions for new topic
            logger.info(f"Generating questions for new topic: {topic_name}")
            from .question_generator import QuestionGenerationService
            question_service = QuestionGenerationService()
            questions = await question_service.generate_topic_questions(topic_name, topic_context)
            
            if not questions:
                logger.error(f"Failed to generate questions for topic {topic_name}")
                return False
            
            # Store questions in Firebase
            success = await question_service.store_questions_in_firebase(user_id, topic_id, questions)
            
            if success:
                logger.info(f"Successfully initialized question bank for topic {topic_name} ({len(questions)} questions)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error ensuring topic {topic_id} has questions: {e}")
            return False
    
    async def get_next_question(self, user_id: str, topic_id: str) -> Optional[Dict]:
        """Get next unused question for topic"""
        try:
            unused_questions = await self.get_unused_questions(user_id, topic_id, limit=1)
            return unused_questions[0] if unused_questions else None
        except Exception as e:
            logger.error(f"Error getting next question for topic {topic_id}: {e}")
            return None
    
    async def get_unused_questions(self, user_id: str, topic_id: str, limit: int = 7) -> List[Dict]:
        """Retrieve unused questions for a topic"""
        try:
            questions_ref = (
                self._db
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
    
    async def store_question_summary(self, user_id: str, topic_id: str, question_id: str, summary: Dict) -> bool:
        """Store conversation summary for a question"""
        try:
            summary_ref = (
                self._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
                .collection('question_summaries')
                .document(question_id)
            )
            
            summary_data = {
                **summary,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'question_id': question_id,
                'topic_id': topic_id
            }
            
            summary_ref.set(summary_data)
            logger.info(f"Stored question summary for {question_id} in topic {topic_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing question summary for {question_id}: {e}")
            return False
    
    async def get_topic_question_summaries(self, user_id: str, topic_id: str) -> List[Dict]:
        """Get all question summaries for topic evaluation"""
        try:
            summaries_ref = (
                self._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
                .collection('question_summaries')
            )
            
            docs = summaries_ref.stream()
            summaries = []
            
            for doc in docs:
                summary_data = doc.to_dict()
                summary_data['id'] = doc.id
                summaries.append(summary_data)
            
            logger.info(f"Retrieved {len(summaries)} question summaries for topic {topic_id}")
            return summaries
            
        except Exception as e:
            logger.error(f"Error retrieving question summaries for topic {topic_id}: {e}")
            return []
    
    async def mark_question_used(self, user_id: str, topic_id: str, question_id: str) -> bool:
        """Mark a question as used"""
        try:
            question_ref = (
                self._db
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
                'usage_count': 1
            })
            
            # Update topic metadata with proper imports
            topic_ref = (
                self._db
                .collection('users')
                .document(user_id)
                .collection('question_banks')
                .document(topic_id)
            )
            
            # Use Firestore increments for atomic updates
            topic_ref.update({
                'questions_used': firestore.Increment(1),
                'questions_remaining': firestore.Increment(-1),
                'last_accessed': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Marked question {question_id} as used for topic {topic_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking question {question_id} as used: {e}")
            return False


# Global Firebase service instance
firebase_service = FirebaseService() 