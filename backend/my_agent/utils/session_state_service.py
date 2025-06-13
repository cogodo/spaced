"""
Session State Service for Phase 4: Persistent Adaptive Intelligence State Management

This service handles saving, loading, and synchronizing Phase 4 adaptive intelligence state
with Firebase for session resumption and real-time state management.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import json

from .firebase_service import FirebaseService
from .state import GraphState

logger = logging.getLogger(__name__)


class SessionStateService:
    """Service for managing persistent adaptive intelligence state"""
    
    def __init__(self, firebase_service: Optional[FirebaseService] = None):
        self.firebase_service = firebase_service or FirebaseService()
    
    async def save_adaptive_state(self, session_id: str, user_id: str, state: GraphState) -> bool:
        """
        Save Phase 4 adaptive intelligence state to Firebase
        
        Args:
            session_id: Session identifier
            user_id: User identifier  
            state: Current GraphState with adaptive fields
            
        Returns:
            Success status
        """
        try:
            # Extract adaptive intelligence fields
            adaptive_data = self._extract_adaptive_state(state)
            
            # Add metadata
            adaptive_data.update({
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "schema_version": 2,  # Phase 4 schema version
                "state_type": "adaptive_intelligence"
            })
            
            # Save to Firebase: users/{user_id}/chatSessions/{session_id}/adaptiveState
            adaptive_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('adaptiveState')
                .document('current')
            )
            
            adaptive_ref.set(adaptive_data)
            
            logger.info(f"Saved adaptive state for session {session_id} (user: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving adaptive state for session {session_id}: {e}")
            return False
    
    async def restore_adaptive_state(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """
        Restore Phase 4 adaptive intelligence state from Firebase
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Restored adaptive state dictionary
        """
        try:
            # Load from Firebase
            adaptive_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('adaptiveState')
                .document('current')
            )
            
            doc = adaptive_ref.get()
            
            if not doc.exists:
                logger.info(f"No adaptive state found for session {session_id}, returning defaults")
                return self._get_default_adaptive_state()
            
            adaptive_data = doc.to_dict()
            
            # Handle schema migration if needed
            schema_version = adaptive_data.get("schema_version", 1)
            if schema_version < 2:
                adaptive_data = self._migrate_adaptive_state(adaptive_data)
            
            logger.info(f"Restored adaptive state for session {session_id} (user: {user_id})")
            return adaptive_data
            
        except Exception as e:
            logger.error(f"Error restoring adaptive state for session {session_id}: {e}")
            return self._get_default_adaptive_state()
    
    async def save_question_adaptation_history(self, session_id: str, user_id: str, 
                                             adaptation_entry: Dict[str, Any]) -> bool:
        """
        Save question adaptation decision to history for analytics
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            adaptation_entry: Question adaptation data
            
        Returns:
            Success status
        """
        try:
            # Save to Firebase: users/{user_id}/chatSessions/{session_id}/questionAdaptationHistory/{timestamp}
            history_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('questionAdaptationHistory')
            )
            
            # Add timestamp if not present
            adaptation_entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            
            # Add document
            history_ref.add(adaptation_entry)
            
            logger.debug(f"Saved question adaptation history for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving question adaptation history: {e}")
            return False
    
    async def get_session_optimization_log(self, session_id: str, user_id: str, 
                                         limit: int = 50) -> list[Dict[str, Any]]:
        """
        Get session optimization log for analytics
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            limit: Maximum number of entries to return
            
        Returns:
            List of optimization log entries
        """
        try:
            history_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('questionAdaptationHistory')
            )
            
            # Query recent entries
            query = history_ref.order_by('timestamp', direction='DESCENDING').limit(limit)
            docs = query.stream()
            
            optimization_log = []
            for doc in docs:
                entry = doc.to_dict()
                entry['id'] = doc.id
                optimization_log.append(entry)
            
            logger.info(f"Retrieved {len(optimization_log)} optimization log entries")
            return optimization_log
            
        except Exception as e:
            logger.error(f"Error getting session optimization log: {e}")
            return []
    
    def _extract_adaptive_state(self, state: GraphState) -> Dict[str, Any]:
        """Extract Phase 4 adaptive intelligence fields from GraphState"""
        
        adaptive_fields = {
            # Core adaptive intelligence
            "live_performance_metrics": state.get("live_performance_metrics"),
            "adaptive_difficulty_level": state.get("adaptive_difficulty_level"),
            "learned_user_preferences": state.get("learned_user_preferences"),
            "detected_learning_style": state.get("detected_learning_style"),
            "cognitive_load_level": state.get("cognitive_load_level"),
            "engagement_trend": state.get("engagement_trend"),
            "learning_momentum_score": state.get("learning_momentum_score"),
            
            # Advanced features
            "conversation_intelligence": state.get("conversation_intelligence"),
            "adaptive_conversation_history": state.get("adaptive_conversation_history"),
            "personalization_insights": state.get("personalization_insights"),
            "question_adaptation_history": state.get("question_adaptation_history"),
            "session_optimization_log": state.get("session_optimization_log"),
            
            # Real-time adaptation
            "understanding_velocity": state.get("understanding_velocity"),
            "optimal_question_sequence": state.get("optimal_question_sequence"),
        }
        
        # Remove None values to keep clean data
        return {k: v for k, v in adaptive_fields.items() if v is not None}
    
    def _get_default_adaptive_state(self) -> Dict[str, Any]:
        """Get default adaptive state for new sessions"""
        return {
            "live_performance_metrics": {
                "understanding_history": [],
                "confidence_history": [],
                "engagement_history": [],
                "current_understanding": 0.5,
                "current_confidence": 0.5,
                "current_engagement": 0.5,
                "performance_trend": "stable",
                "session_average": 0.5
            },
            "learned_user_preferences": {
                "learning_style_signals": {},
                "communication_preferences": {},
                "cognitive_patterns": {},
                "motivation_factors": {},
                "discovery_count": 0
            },
            "detected_learning_style": "mixed",
            "cognitive_load_level": "moderate",
            "engagement_trend": "stable",
            "adaptive_difficulty_level": 0.5,
            "learning_momentum_score": 0.5,
            "conversation_intelligence": {},
            "adaptive_conversation_history": [],
            "personalization_insights": {},
            "question_adaptation_history": [],
            "session_optimization_log": [],
            "schema_version": 2,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def _migrate_adaptive_state(self, old_state: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate adaptive state from older schema versions"""
        try:
            # Start with default state
            new_state = self._get_default_adaptive_state()
            
            # Migrate known fields from old state
            for key, value in old_state.items():
                if key in new_state and value is not None:
                    new_state[key] = value
            
            # Update schema version
            new_state["schema_version"] = 2
            new_state["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            logger.info("Migrated adaptive state to schema version 2")
            return new_state
            
        except Exception as e:
            logger.error(f"Error migrating adaptive state: {e}")
            return self._get_default_adaptive_state()
    
    async def clear_session_state(self, session_id: str, user_id: str) -> bool:
        """
        Clear all adaptive state for a session (useful for cleanup)
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            # Delete adaptive state document
            adaptive_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('adaptiveState')
                .document('current')
            )
            
            adaptive_ref.delete()
            
            # Delete adaptation history collection
            history_ref = (
                self.firebase_service._db
                .collection('users')
                .document(user_id)
                .collection('chatSessions')
                .document(session_id)
                .collection('questionAdaptationHistory')
            )
            
            # Delete all documents in history collection
            docs = history_ref.stream()
            batch = self.firebase_service._db.batch()
            
            for doc in docs:
                batch.delete(doc.reference)
            
            batch.commit()
            
            logger.info(f"Cleared adaptive state for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing session state: {e}")
            return False
    
    async def validate_adaptive_state(self, adaptive_state: Dict[str, Any]) -> bool:
        """
        Validate adaptive state structure and data integrity
        
        Args:
            adaptive_state: Adaptive state dictionary to validate
            
        Returns:
            Validation success status
        """
        try:
            required_fields = [
                "live_performance_metrics",
                "learned_user_preferences", 
                "detected_learning_style",
                "adaptive_difficulty_level",
                "learning_momentum_score"
            ]
            
            # Check required fields exist
            for field in required_fields:
                if field not in adaptive_state:
                    logger.warning(f"Adaptive state missing required field: {field}")
                    return False
            
            # Validate live_performance_metrics structure
            metrics = adaptive_state.get("live_performance_metrics", {})
            required_metrics = ["current_understanding", "current_confidence", "current_engagement"]
            
            for metric in required_metrics:
                if metric not in metrics:
                    logger.warning(f"Live performance metrics missing: {metric}")
                    return False
                
                # Validate range
                value = metrics[metric]
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    logger.warning(f"Invalid {metric} value: {value}")
                    return False
            
            # Validate difficulty level
            difficulty = adaptive_state.get("adaptive_difficulty_level", 0.5)
            if not isinstance(difficulty, (int, float)) or difficulty < 0 or difficulty > 1:
                logger.warning(f"Invalid adaptive difficulty level: {difficulty}")
                return False
            
            logger.debug("Adaptive state validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating adaptive state: {e}")
            return False 