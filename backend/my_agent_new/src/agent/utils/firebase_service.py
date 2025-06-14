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
        """Sort tasks by priority: difficulty descending, overdue days descending"""
        def priority_key(task: Task) -> tuple:
            # Higher difficulty = higher priority (sort descending)
            # More overdue days = higher priority (sort descending)
            return (-task.difficulty, -task.days_overdue)
        
        return sorted(tasks, key=priority_key)
    
    async def update_task_after_review(self, user_id: str, task_name: str, score: int, 
                                     session_data: Optional[Dict] = None) -> bool:
        """Update task data after review with FSRS calculations"""
        try:
            task_ref = self._db.collection('users').document(user_id).collection('tasks').document(task_name)
            
            # For now, store the review result
            # FSRS calculations would be implemented in frontend or separate service
            update_data = {
                'lastReviewDate': datetime.now(timezone.utc).isoformat(),
                'lastScore': score,
                'lastSessionData': session_data or {}
            }
            
            task_ref.update(update_data)
            logger.info(f"Updated task {task_name} for user {user_id} with score {score}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task {task_name} for user {user_id}: {e}")
            return False
    
    async def save_session_metrics(self, metrics: SessionMetrics) -> bool:
        """Save comprehensive session metrics to Firestore"""
        try:
            session_ref = self._db.collection('session_analytics').document(metrics.session_id)
            
            # Convert dataclass to dict for Firestore
            metrics_dict = asdict(metrics)
            # Convert datetime objects to ISO strings
            metrics_dict['start_time'] = metrics.start_time.isoformat()
            metrics_dict['end_time'] = metrics.end_time.isoformat()
            
            session_ref.set(metrics_dict)
            
            # Update user stats
            await self._update_user_stats(metrics)
            
            logger.info(f"Session metrics saved for session {metrics.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session metrics: {e}")
            return False
    
    async def _update_user_stats(self, metrics: SessionMetrics) -> None:
        """Update user-level statistics with session data"""
        try:
            user_stats_ref = self._db.collection('user_stats').document(metrics.user_id)
            
            # Use Firestore transaction to update stats atomically
            @firestore.transactional
            def update_stats(transaction, stats_ref):
                doc = stats_ref.get(transaction=transaction)
                current_stats = doc.to_dict() if doc.exists else {}
                
                # Update various statistics
                current_stats['total_sessions'] = current_stats.get('total_sessions', 0) + 1
                current_stats['total_study_time_minutes'] = current_stats.get('total_study_time_minutes', 0) + (metrics.duration_seconds / 60)
                current_stats['last_session_date'] = metrics.end_time.isoformat()
                
                transaction.set(stats_ref, current_stats, merge=True)
            
            transaction = self._db.transaction()
            update_stats(transaction, user_stats_ref)
            
        except Exception as e:
            logger.error(f"Error updating user stats: {e}")
    
    async def get_learning_insights(self, user_id: str, days: int = 30) -> Optional[LearningInsights]:
        """Get comprehensive learning insights for user"""
        try:
            # Get recent sessions
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            sessions_ref = self._db.collection('session_analytics').where('user_id', '==', user_id).where('end_time', '>=', cutoff_date.isoformat())
            sessions = sessions_ref.stream()
            
            sessions_data = [doc.to_dict() for doc in sessions]
            
            if not sessions_data:
                return None
            
            return self._analyze_sessions(user_id, sessions_data, days)
            
        except Exception as e:
            logger.error(f"Error getting learning insights for user {user_id}: {e}")
            return None
    
    def _analyze_sessions(self, user_id: str, sessions_data: List[Dict], days: int) -> LearningInsights:
        """Analyze session data to generate insights"""
        total_sessions = len(sessions_data)
        due_items_sessions = sum(1 for s in sessions_data if s.get('session_type') == 'due_items')
        custom_topics_sessions = total_sessions - due_items_sessions
        
        # Calculate total study time
        total_study_time_minutes = sum(s.get('duration_seconds', 0) for s in sessions_data) / 60
        avg_session_duration = total_study_time_minutes / total_sessions if total_sessions > 0 else 0
        
        # Analyze scores by topic
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
        
        # Calculate averages and trends
        average_scores = {topic: sum(scores) / len(scores) for topic, scores in all_scores.items()}
        
        # Calculate improvement rates (simple linear trend)
        improvement_rate = {}
        for topic, scores in score_trends.items():
            if len(scores) >= 2:
                # Simple improvement rate: (last_score - first_score) / sessions
                improvement_rate[topic] = (scores[-1] - scores[0]) / len(scores)
            else:
                improvement_rate[topic] = 0.0
        
        # Identify struggling and mastered topics
        struggling_topics = [topic for topic, avg in average_scores.items() if avg < 3.0]
        mastered_topics = [topic for topic, avg in average_scores.items() if avg >= 4.5]
        
        # Simple review frequency recommendations
        recommended_review_frequency = {}
        for topic, avg_score in average_scores.items():
            if avg_score >= 4.5:
                recommended_review_frequency[topic] = 7  # Weekly for mastered topics
            elif avg_score >= 3.5:
                recommended_review_frequency[topic] = 3  # Every 3 days for good topics
            else:
                recommended_review_frequency[topic] = 1  # Daily for struggling topics
        
        return LearningInsights(
            user_id=user_id,
            analysis_period_days=days,
            total_sessions=total_sessions,
            due_items_sessions=due_items_sessions,
            custom_topics_sessions=custom_topics_sessions,
            total_study_time_minutes=int(total_study_time_minutes),
            avg_session_duration_minutes=avg_session_duration,
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
            # Get user stats
            user_stats_ref = self._db.collection('user_stats').document(user_id)
            stats_doc = user_stats_ref.get()
            stats = stats_doc.to_dict() if stats_doc.exists else {}
            
            # Get due tasks count
            due_tasks = await self.get_due_tasks(user_id)
            due_count = len(due_tasks)
            
            # Get recent learning insights
            insights = await self.get_learning_insights(user_id, days=7)
            
            return {
                'user_stats': stats,
                'due_tasks_count': due_count,
                'recent_insights': asdict(insights) if insights else None,
                'due_tasks_preview': [
                    {
                        'task_name': task.task_name,
                        'difficulty': task.difficulty,
                        'days_overdue': task.days_overdue
                    } for task in due_tasks[:5]  # First 5 tasks
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {e}")
            return {}
    
    async def get_topic_questions(self, user_id: str, topic_id: str) -> Dict[str, Any]:
        """Get questions for a specific topic"""
        try:
            questions_ref = self._db.collection('users').document(user_id).collection('topic_questions').document(topic_id)
            doc = questions_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return {"questions": []}
                
        except Exception as e:
            logger.error(f"Error getting questions for topic {topic_id}: {e}")
            return {"questions": []}


class QuestionBankService:
    """Service for managing topic-specific question banks"""
    
    def __init__(self, firebase_service: FirebaseService = None):
        self.firebase = firebase_service or FirebaseService()
    
    async def ensure_topic_has_questions(self, user_id: str, topic_id: str, topic_name: str, topic_context: str = "") -> bool:
        """Ensure a topic has questions available, generating them if necessary"""
        try:
            # Check if questions already exist
            existing_questions = await self.firebase.get_topic_questions(user_id, topic_id)
            
            if existing_questions.get("questions") and len(existing_questions["questions"]) >= 5:
                return True
            
            # Generate questions if needed
            # This would typically involve calling an AI service to generate questions
            # For now, we'll create placeholder questions
            questions = [
                {
                    "id": f"{topic_id}_q{i}",
                    "text": f"Question {i+1} about {topic_name}",
                    "type": "free_recall",
                    "difficulty": 0.5,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "used": False
                }
                for i in range(7)
            ]
            
            # Save questions
            questions_ref = self.firebase._db.collection('users').document(user_id).collection('topic_questions').document(topic_id)
            questions_ref.set({
                "topic_name": topic_name,
                "topic_context": topic_context,
                "questions": questions,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring questions for topic {topic_id}: {e}")
            return False
    
    async def get_next_question(self, user_id: str, topic_id: str) -> Optional[Dict]:
        """Get the next unused question for a topic"""
        unused_questions = await self.get_unused_questions(user_id, topic_id, limit=1)
        return unused_questions[0] if unused_questions else None
    
    async def get_unused_questions(self, user_id: str, topic_id: str, limit: int = 7) -> List[Dict]:
        """Get unused questions for a topic"""
        try:
            topic_questions = await self.firebase.get_topic_questions(user_id, topic_id)
            all_questions = topic_questions.get("questions", [])
            
            # Filter unused questions
            unused = [q for q in all_questions if not q.get("used", False)]
            
            # Return up to limit
            return unused[:limit]
            
        except Exception as e:
            logger.error(f"Error getting unused questions for topic {topic_id}: {e}")
            return []
    
    async def store_question_summary(self, user_id: str, topic_id: str, question_id: str, summary: Dict) -> bool:
        """Store a summary of a question interaction"""
        try:
            summary_ref = self.firebase._db.collection('users').document(user_id).collection('question_summaries').document(f"{topic_id}_{question_id}")
            
            summary_data = {
                "topic_id": topic_id,
                "question_id": question_id,
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            summary_ref.set(summary_data)
            return True
            
        except Exception as e:
            logger.error(f"Error storing question summary: {e}")
            return False
    
    async def get_topic_question_summaries(self, user_id: str, topic_id: str) -> List[Dict]:
        """Get all question summaries for a topic"""
        try:
            summaries_ref = self.firebase._db.collection('users').document(user_id).collection('question_summaries').where('topic_id', '==', topic_id)
            docs = summaries_ref.stream()
            
            summaries = []
            for doc in docs:
                data = doc.to_dict()
                summaries.append(data)
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting question summaries for topic {topic_id}: {e}")
            return []
    
    async def mark_question_used(self, user_id: str, topic_id: str, question_id: str) -> bool:
        """Mark a question as used"""
        try:
            questions_ref = self.firebase._db.collection('users').document(user_id).collection('topic_questions').document(topic_id)
            doc = questions_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                questions = data.get("questions", [])
                
                # Find and mark the question as used
                for question in questions:
                    if question.get("id") == question_id:
                        question["used"] = True
                        question["used_at"] = datetime.now(timezone.utc).isoformat()
                        break
                
                # Update the document
                questions_ref.update({"questions": questions})
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking question {question_id} as used: {e}")
            return False


# Global instance
firebase_service = FirebaseService() 