"""
Adaptive State Integration for Phase 4: Real-time State Persistence

This module provides integration hooks to automatically save adaptive intelligence state
after every user response in the conversation flow.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import asyncio

from .session_state_service import SessionStateService
from .state import GraphState

logger = logging.getLogger(__name__)


class AdaptiveStateIntegration:
    """Integration layer for real-time adaptive state persistence"""
    
    def __init__(self):
        self.state_service = SessionStateService()
        self._save_queue = asyncio.Queue()
        self._is_processing = False
    
    async def save_state_after_response(self, state: GraphState) -> bool:
        """
        Save adaptive state after user response with error handling
        
        Args:
            state: Current GraphState with updated adaptive intelligence fields
            
        Returns:
            Success status
        """
        try:
            session_id = self._extract_session_id(state)
            user_id = state.get("user_id")
            
            if not session_id or not user_id:
                logger.warning("Cannot save adaptive state: missing session_id or user_id")
                return False
            
            # Save adaptive state
            success = await self.state_service.save_adaptive_state(session_id, user_id, state)
            
            # Save question adaptation history if present
            if state.get("question_adaptation_history"):
                await self._save_adaptation_history(session_id, user_id, state)
            
            if success:
                logger.debug(f"Adaptive state saved for session {session_id}")
            else:
                logger.warning(f"Failed to save adaptive state for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in save_state_after_response: {e}")
            return False
    
    async def restore_state_on_session_load(self, session_id: str, user_id: str, state: GraphState) -> bool:
        """
        Restore adaptive state when loading an existing session
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            state: GraphState to populate with restored adaptive state
            
        Returns:
            Success status
        """
        try:
            # Restore adaptive state
            adaptive_state = await self.state_service.restore_adaptive_state(session_id, user_id)
            
            # Populate state with restored adaptive intelligence fields
            self._populate_state_with_adaptive_data(state, adaptive_state)
            
            # Load optimization history for analytics
            optimization_log = await self.state_service.get_session_optimization_log(
                session_id, user_id, limit=20
            )
            state["session_optimization_log"] = optimization_log
            
            logger.info(f"Restored adaptive state for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring adaptive state for session {session_id}: {e}")
            # Initialize with defaults on restore failure
            self._initialize_default_adaptive_state(state)
            return False
    
    async def log_adaptation_decision(self, state: GraphState, adaptation_type: str, 
                                    adaptation_data: Dict[str, Any]) -> None:
        """
        Log adaptation decisions for analytics and debugging
        
        Args:
            state: Current GraphState
            adaptation_type: Type of adaptation (question_selection, difficulty_adjustment, etc.)
            adaptation_data: Data about the adaptation decision
        """
        try:
            session_id = self._extract_session_id(state)
            user_id = state.get("user_id")
            
            if not session_id or not user_id:
                return
            
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "adaptation_type": adaptation_type,
                "adaptation_data": adaptation_data,
                "session_context": {
                    "current_understanding": state.get("live_performance_metrics", {}).get("current_understanding", 0.5),
                    "learning_momentum": state.get("learning_momentum_score", 0.5),
                    "detected_learning_style": state.get("detected_learning_style", "mixed"),
                    "adaptive_difficulty": state.get("adaptive_difficulty_level", 0.5)
                }
            }
            
            await self.state_service.save_question_adaptation_history(session_id, user_id, log_entry)
            
            # Also add to state for immediate access
            if "session_optimization_log" not in state:
                state["session_optimization_log"] = []
            state["session_optimization_log"].append(log_entry)
            
            # Keep local log manageable
            if len(state["session_optimization_log"]) > 50:
                state["session_optimization_log"] = state["session_optimization_log"][-50:]
            
        except Exception as e:
            logger.error(f"Error logging adaptation decision: {e}")
    
    async def validate_and_repair_state(self, state: GraphState) -> bool:
        """
        Validate adaptive state and repair any issues
        
        Args:
            state: GraphState to validate and repair
            
        Returns:
            True if state is valid or was successfully repaired
        """
        try:
            # Extract current adaptive state
            adaptive_data = self.state_service._extract_adaptive_state(state)
            
            # Validate structure
            is_valid = await self.state_service.validate_adaptive_state(adaptive_data)
            
            if not is_valid:
                logger.warning("Invalid adaptive state detected, attempting repair")
                self._repair_adaptive_state(state)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating adaptive state: {e}")
            self._initialize_default_adaptive_state(state)
            return False
    
    def _extract_session_id(self, state: GraphState) -> Optional[str]:
        """Extract session ID from various possible state locations"""
        
        # Try different possible locations for session ID
        session_id = (
            state.get("session_id") or
            state.get("current_session_id") or
            state.get("id")
        )
        
        return session_id
    
    def _populate_state_with_adaptive_data(self, state: GraphState, adaptive_data: Dict[str, Any]) -> None:
        """Populate GraphState with restored adaptive intelligence data"""
        
        # Core adaptive intelligence fields
        adaptive_fields = [
            "live_performance_metrics",
            "adaptive_difficulty_level", 
            "learned_user_preferences",
            "detected_learning_style",
            "cognitive_load_level",
            "engagement_trend",
            "learning_momentum_score",
            "conversation_intelligence",
            "adaptive_conversation_history",
            "personalization_insights",
            "question_adaptation_history",
            "understanding_velocity",
            "optimal_question_sequence"
        ]
        
        for field in adaptive_fields:
            if field in adaptive_data:
                state[field] = adaptive_data[field]
    
    def _initialize_default_adaptive_state(self, state: GraphState) -> None:
        """Initialize state with default adaptive intelligence values"""
        
        default_state = self.state_service._get_default_adaptive_state()
        self._populate_state_with_adaptive_data(state, default_state)
        
        logger.info("Initialized default adaptive state")
    
    def _repair_adaptive_state(self, state: GraphState) -> None:
        """Repair corrupted or incomplete adaptive state"""
        
        # Get current adaptive data
        current_adaptive = self.state_service._extract_adaptive_state(state)
        
        # Get default state as template
        default_state = self.state_service._get_default_adaptive_state()
        
        # Merge current with defaults, prioritizing valid current data
        repaired_state = default_state.copy()
        
        for key, value in current_adaptive.items():
            if value is not None:
                repaired_state[key] = value
        
        # Validate critical metrics
        metrics = repaired_state.get("live_performance_metrics", {})
        for metric in ["current_understanding", "current_confidence", "current_engagement"]:
            if metric not in metrics or not isinstance(metrics[metric], (int, float)):
                metrics[metric] = 0.5
            else:
                # Clamp to valid range
                metrics[metric] = max(0.0, min(1.0, metrics[metric]))
        
        # Populate state with repaired data
        self._populate_state_with_adaptive_data(state, repaired_state)
        
        logger.info("Repaired adaptive state with valid defaults")
    
    async def _save_adaptation_history(self, session_id: str, user_id: str, state: GraphState) -> None:
        """Save question adaptation history entries"""
        
        try:
            adaptation_history = state.get("question_adaptation_history", [])
            
            # Save only new entries (those without an id)
            for entry in adaptation_history:
                if not entry.get("id"):  # New entry without Firebase ID
                    await self.state_service.save_question_adaptation_history(
                        session_id, user_id, entry
                    )
            
        except Exception as e:
            logger.error(f"Error saving adaptation history: {e}")


# Global instance for easy access
adaptive_state_integration = AdaptiveStateIntegration()


# Convenience functions for node integration
async def auto_save_adaptive_state(state: GraphState) -> bool:
    """
    Convenience function for nodes to automatically save adaptive state
    
    Args:
        state: Current GraphState
        
    Returns:
        Success status
    """
    return await adaptive_state_integration.save_state_after_response(state)


async def auto_restore_adaptive_state(session_id: str, user_id: str, state: GraphState) -> bool:
    """
    Convenience function to restore adaptive state on session load
    
    Args:
        session_id: Session identifier
        user_id: User identifier  
        state: GraphState to populate
        
    Returns:
        Success status
    """
    return await adaptive_state_integration.restore_state_on_session_load(session_id, user_id, state)


async def log_adaptive_decision(state: GraphState, adaptation_type: str, data: Dict[str, Any]) -> None:
    """
    Convenience function to log adaptation decisions
    
    Args:
        state: Current GraphState
        adaptation_type: Type of adaptation
        data: Adaptation data
    """
    await adaptive_state_integration.log_adaptation_decision(state, adaptation_type, data) 