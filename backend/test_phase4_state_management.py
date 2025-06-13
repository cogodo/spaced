#!/usr/bin/env python3
"""
Comprehensive tests for Phase 4: State Management & Database Integration
"""

import pytest
import asyncio
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

# Set test environment before importing modules
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['FIREBASE_PROJECT_ID'] = 'test-project'

from my_agent.utils.session_state_service import SessionStateService
from my_agent.utils.adaptive_state_integration import (
    AdaptiveStateIntegration, 
    auto_save_adaptive_state,
    auto_restore_adaptive_state,
    log_adaptive_decision
)
from my_agent.utils.state import GraphState


class TestSessionStateService:
    """Test suite for SessionStateService"""
    
    @pytest.fixture
    def mock_firebase_service(self):
        """Mock Firebase service for testing"""
        mock_service = Mock()
        mock_service._db = Mock()
        return mock_service
    
    @pytest.fixture
    def session_state_service(self, mock_firebase_service):
        """Create SessionStateService with mocked Firebase"""
        return SessionStateService(firebase_service=mock_firebase_service)
    
    @pytest.fixture
    def sample_adaptive_state(self):
        """Sample adaptive state for testing"""
        return {
            "live_performance_metrics": {
                "understanding_history": [0.5, 0.6, 0.7],
                "confidence_history": [0.4, 0.6, 0.8],
                "engagement_history": [0.7, 0.8, 0.9],
                "current_understanding": 0.7,
                "current_confidence": 0.8,
                "current_engagement": 0.9,
                "performance_trend": "improving",
                "session_average": 0.8
            },
            "learned_user_preferences": {
                "learning_style_signals": {"visual": 0.8, "analytical": 0.6},
                "communication_preferences": {"detail_level": "moderate"},
                "cognitive_patterns": {"processing_speed": "fast"},
                "motivation_factors": {"challenge_seeking": 0.7},
                "discovery_count": 5
            },
            "detected_learning_style": "visual",
            "cognitive_load_level": "moderate",
            "engagement_trend": "improving",
            "adaptive_difficulty_level": 0.6,
            "learning_momentum_score": 0.7
        }
    
    @pytest.fixture
    def sample_graph_state(self, sample_adaptive_state):
        """Sample GraphState with adaptive fields"""
        state = {
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "user_input": "This is a test response"
        }
        state.update(sample_adaptive_state)
        return state
    
    @pytest.mark.asyncio
    async def test_save_adaptive_state_success(self, session_state_service, sample_graph_state):
        """Test successful adaptive state saving"""
        # Mock successful Firestore operation
        mock_doc_ref = Mock()
        session_state_service.firebase_service._db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref
        
        # Test save operation
        result = await session_state_service.save_adaptive_state(
            session_id="test-session-123",
            user_id="test-user-456", 
            state=sample_graph_state
        )
        
        assert result is True
        mock_doc_ref.set.assert_called_once()
        
        # Verify saved data structure
        call_args = mock_doc_ref.set.call_args[0][0]
        assert "live_performance_metrics" in call_args
        assert "learned_user_preferences" in call_args
        assert "schema_version" in call_args
        assert call_args["schema_version"] == 2
        assert "last_updated" in call_args
    
    @pytest.mark.asyncio
    async def test_save_adaptive_state_failure(self, session_state_service, sample_graph_state):
        """Test adaptive state saving failure handling"""
        # Mock Firestore exception
        session_state_service.firebase_service._db.collection.side_effect = Exception("Firebase error")
        
        result = await session_state_service.save_adaptive_state(
            session_id="test-session-123",
            user_id="test-user-456",
            state=sample_graph_state
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_restore_adaptive_state_success(self, session_state_service, sample_adaptive_state):
        """Test successful adaptive state restoration"""
        # Mock successful Firestore retrieval
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = sample_adaptive_state
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        session_state_service.firebase_service._db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref
        
        # Test restore operation
        result = await session_state_service.restore_adaptive_state(
            session_id="test-session-123",
            user_id="test-user-456"
        )
        
        assert "live_performance_metrics" in result
        assert "learned_user_preferences" in result
        assert result["detected_learning_style"] == "visual"
        assert result["adaptive_difficulty_level"] == 0.6
    
    @pytest.mark.asyncio
    async def test_restore_adaptive_state_not_found(self, session_state_service):
        """Test adaptive state restoration when no state exists"""
        # Mock document not found
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        session_state_service.firebase_service._db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_doc_ref
        
        # Test restore operation
        result = await session_state_service.restore_adaptive_state(
            session_id="test-session-123",
            user_id="test-user-456"
        )
        
        # Should return default state
        assert "live_performance_metrics" in result
        assert result["detected_learning_style"] == "mixed"
        assert result["adaptive_difficulty_level"] == 0.5
        assert result["schema_version"] == 2
    
    @pytest.mark.asyncio
    async def test_validate_adaptive_state_valid(self, session_state_service, sample_adaptive_state):
        """Test validation of valid adaptive state"""
        result = await session_state_service.validate_adaptive_state(sample_adaptive_state)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_adaptive_state_invalid(self, session_state_service):
        """Test validation of invalid adaptive state"""
        invalid_state = {
            "live_performance_metrics": {
                "current_understanding": 1.5,  # Invalid - out of range
                "current_confidence": -0.1,   # Invalid - out of range
                "current_engagement": "high"   # Invalid - not numeric
            },
            "adaptive_difficulty_level": "medium"  # Invalid - not numeric
        }
        
        result = await session_state_service.validate_adaptive_state(invalid_state)
        assert result is False
    
    def test_extract_adaptive_state(self, session_state_service, sample_graph_state):
        """Test extraction of adaptive state from GraphState"""
        result = session_state_service._extract_adaptive_state(sample_graph_state)
        
        assert "live_performance_metrics" in result
        assert "learned_user_preferences" in result
        assert "detected_learning_style" in result
        assert "adaptive_difficulty_level" in result
        assert "learning_momentum_score" in result
        
        # Should not include non-adaptive fields
        assert "user_input" not in result
        assert "session_id" not in result
    
    def test_get_default_adaptive_state(self, session_state_service):
        """Test default adaptive state generation"""
        result = session_state_service._get_default_adaptive_state()
        
        # Verify structure
        assert "live_performance_metrics" in result
        assert "learned_user_preferences" in result
        assert "detected_learning_style" in result
        assert "adaptive_difficulty_level" in result
        assert "learning_momentum_score" in result
        assert "schema_version" in result
        
        # Verify default values
        assert result["detected_learning_style"] == "mixed"
        assert result["adaptive_difficulty_level"] == 0.5
        assert result["learning_momentum_score"] == 0.5
        assert result["schema_version"] == 2
        
        # Verify metrics structure
        metrics = result["live_performance_metrics"]
        assert metrics["current_understanding"] == 0.5
        assert metrics["current_confidence"] == 0.5
        assert metrics["current_engagement"] == 0.5


class TestAdaptiveStateIntegration:
    """Test suite for AdaptiveStateIntegration"""
    
    @pytest.fixture
    def integration(self):
        """Create AdaptiveStateIntegration instance"""
        with patch('my_agent.utils.adaptive_state_integration.SessionStateService'):
            return AdaptiveStateIntegration()
    
    @pytest.fixture
    def sample_graph_state(self):
        """Sample GraphState for testing"""
        return {
            "session_id": "test-session-123",
            "user_id": "test-user-456",
            "user_input": "This is a test response",
            "live_performance_metrics": {
                "current_understanding": 0.7,
                "current_confidence": 0.8,
                "current_engagement": 0.9
            },
            "adaptive_difficulty_level": 0.6,
            "detected_learning_style": "visual",
            "learning_momentum_score": 0.7
        }
    
    @pytest.mark.asyncio
    async def test_save_state_after_response_success(self, integration, sample_graph_state):
        """Test successful state saving after response"""
        # Mock successful save
        integration.state_service.save_adaptive_state = AsyncMock(return_value=True)
        
        result = await integration.save_state_after_response(sample_graph_state)
        
        assert result is True
        integration.state_service.save_adaptive_state.assert_called_once_with(
            "test-session-123", "test-user-456", sample_graph_state
        )
    
    @pytest.mark.asyncio 
    async def test_save_state_after_response_missing_ids(self, integration):
        """Test state saving with missing session/user IDs"""
        incomplete_state = {"user_input": "test"}
        
        result = await integration.save_state_after_response(incomplete_state)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_restore_state_on_session_load(self, integration, sample_graph_state):
        """Test state restoration on session load"""
        # Mock successful restore
        integration.state_service.restore_adaptive_state = AsyncMock(return_value={
            "live_performance_metrics": {"current_understanding": 0.7},
            "detected_learning_style": "visual"
        })
        integration.state_service.get_session_optimization_log = AsyncMock(return_value=[])
        
        empty_state = {}
        result = await integration.restore_state_on_session_load(
            "test-session-123", "test-user-456", empty_state
        )
        
        assert result is True
        assert "live_performance_metrics" in empty_state
        assert "detected_learning_style" in empty_state
    
    @pytest.mark.asyncio
    async def test_log_adaptation_decision(self, integration, sample_graph_state):
        """Test adaptation decision logging"""
        # Mock successful logging
        integration.state_service.save_question_adaptation_history = AsyncMock(return_value=True)
        
        adaptation_data = {
            "question_selected": "test-question",
            "difficulty_adjusted": 0.1
        }
        
        await integration.log_adaptation_decision(
            sample_graph_state, "question_selection", adaptation_data
        )
        
        integration.state_service.save_question_adaptation_history.assert_called_once()
        
        # Verify log entry structure
        call_args = integration.state_service.save_question_adaptation_history.call_args[0]
        assert call_args[0] == "test-session-123"  # session_id
        assert call_args[1] == "test-user-456"     # user_id
        
        log_entry = call_args[2]
        assert log_entry["adaptation_type"] == "question_selection"
        assert log_entry["adaptation_data"] == adaptation_data
        assert "session_context" in log_entry
        assert "timestamp" in log_entry
    
    @pytest.mark.asyncio
    async def test_validate_and_repair_state_valid(self, integration, sample_graph_state):
        """Test validation of valid adaptive state"""
        integration.state_service.validate_adaptive_state = AsyncMock(return_value=True)
        
        result = await integration.validate_and_repair_state(sample_graph_state)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_and_repair_state_invalid(self, integration, sample_graph_state):
        """Test validation and repair of invalid adaptive state"""
        integration.state_service.validate_adaptive_state = AsyncMock(return_value=False)
        
        result = await integration.validate_and_repair_state(sample_graph_state)
        
        assert result is False
        # State should be repaired (verify repair was attempted)
        assert "live_performance_metrics" in sample_graph_state


class TestConvenienceFunctions:
    """Test convenience functions for node integration"""
    
    @pytest.fixture
    def sample_state(self):
        return {
            "session_id": "test-session",
            "user_id": "test-user",
            "live_performance_metrics": {"current_understanding": 0.7}
        }
    
    @pytest.mark.asyncio
    @patch('my_agent.utils.adaptive_state_integration.adaptive_state_integration')
    async def test_auto_save_adaptive_state(self, mock_integration, sample_state):
        """Test auto_save_adaptive_state convenience function"""
        mock_integration.save_state_after_response = AsyncMock(return_value=True)
        
        result = await auto_save_adaptive_state(sample_state)
        
        assert result is True
        mock_integration.save_state_after_response.assert_called_once_with(sample_state)
    
    @pytest.mark.asyncio
    @patch('my_agent.utils.adaptive_state_integration.adaptive_state_integration')
    async def test_auto_restore_adaptive_state(self, mock_integration, sample_state):
        """Test auto_restore_adaptive_state convenience function"""
        mock_integration.restore_state_on_session_load = AsyncMock(return_value=True)
        
        result = await auto_restore_adaptive_state("session-123", "user-456", sample_state)
        
        assert result is True
        mock_integration.restore_state_on_session_load.assert_called_once_with(
            "session-123", "user-456", sample_state
        )
    
    @pytest.mark.asyncio
    @patch('my_agent.utils.adaptive_state_integration.adaptive_state_integration')
    async def test_log_adaptive_decision(self, mock_integration, sample_state):
        """Test log_adaptive_decision convenience function"""
        mock_integration.log_adaptation_decision = AsyncMock()
        
        await log_adaptive_decision(sample_state, "test_type", {"key": "value"})
        
        mock_integration.log_adaptation_decision.assert_called_once_with(
            sample_state, "test_type", {"key": "value"}
        )


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios"""
    
    @pytest.mark.asyncio
    @patch('my_agent.utils.adaptive_state_integration.SessionStateService')
    async def test_full_session_workflow(self, mock_service_class):
        """Test complete session workflow with state management"""
        # Setup mock service
        mock_service = Mock()
        mock_service.save_adaptive_state = AsyncMock(return_value=True)
        mock_service.restore_adaptive_state = AsyncMock(return_value={
            "live_performance_metrics": {"current_understanding": 0.5},
            "detected_learning_style": "mixed",
            "adaptive_difficulty_level": 0.5
        })
        mock_service.save_question_adaptation_history = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service
        
        # Create integration
        integration = AdaptiveStateIntegration()
        
        # Simulate session start with state restoration
        session_state = {}
        restore_success = await integration.restore_state_on_session_load(
            "session-123", "user-456", session_state
        )
        
        assert restore_success is True
        assert "live_performance_metrics" in session_state
        
        # Simulate user response processing with state saving
        session_state.update({
            "session_id": "session-123",
            "user_id": "user-456",
            "live_performance_metrics": {"current_understanding": 0.8}
        })
        
        save_success = await integration.save_state_after_response(session_state)
        assert save_success is True
        
        # Verify service calls
        mock_service.restore_adaptive_state.assert_called_once()
        mock_service.save_adaptive_state.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test system resilience to state management errors"""
        with patch('my_agent.utils.adaptive_state_integration.SessionStateService') as mock_service_class:
            # Mock service that always fails
            mock_service = Mock()
            mock_service.save_adaptive_state = AsyncMock(side_effect=Exception("Firebase down"))
            mock_service.restore_adaptive_state = AsyncMock(side_effect=Exception("Firebase down"))
            mock_service_class.return_value = mock_service
            
            integration = AdaptiveStateIntegration()
            
            # Test that failures don't crash the system
            state = {"session_id": "test", "user_id": "test"}
            
            save_result = await integration.save_state_after_response(state)
            assert save_result is False  # Failed but handled gracefully
            
            restore_result = await integration.restore_state_on_session_load("test", "test", state)
            assert restore_result is False  # Failed but handled gracefully
            
            # State should have default values after restore failure
            assert "live_performance_metrics" in state


# Run tests
if __name__ == "__main__":
    print("🧪 Running Phase 4 State Management Tests...")
    
    # Run pytest programmatically
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("✅ All Phase 4 state management tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    
    exit(exit_code) 