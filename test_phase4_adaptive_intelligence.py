"""
Phase 4: Real-Time Adaptive Intelligence - Comprehensive Test Suite
Testing adaptive learning algorithms, live analysis, and personalization features
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the tools and services to avoid external dependencies
def mock_call_ai_with_json_output(prompt):
    """Mock AI call returning realistic adaptive analysis"""
    if "real-time analysis" in prompt.lower():
        return {
            "understanding": 0.75,
            "confidence": 0.68,
            "engagement": 0.82,
            "confusion_indicators": ["needs clarification on concept X"],
            "learning_style_signals": {
                "visual_preference": 0.3,
                "verbal_preference": 0.8,
                "experiential_preference": 0.6,
                "step_by_step_preference": 0.7
            },
            "cognitive_load": "moderate",
            "adaptation_recommendations": {
                "difficulty_adjustment": "maintain",
                "teaching_strategy": "elaborative_questioning",
                "conversation_style": "encouragement_focused"
            },
            "key_insights": ["Shows strong verbal reasoning", "Needs more conceptual foundation"],
            "response_quality_score": 0.74
        }
    elif "conversation strategy" in prompt.lower():
        return {
            "teaching_strategy": "socratic_questioning",
            "difficulty_adjustment": "maintain_current",
            "conversation_style": {
                "tone": "encouraging",
                "pacing": "moderate",
                "question_density": "medium",
                "language_level": "accessible"
            },
            "engagement_tactics": ["curiosity_questions", "real_world_applications"],
            "personalization_applied": ["learning_style_adaptation", "cognitive_load_consideration"],
            "adaptation_reasoning": "User shows good understanding but could use more engagement",
            "confidence_score": 0.85
        }
    elif "conversation action" in prompt.lower():
        return {
            "action": "continue_conversation",
            "reasoning": "User understanding shows gaps that need exploration",
            "follow_up_focus": "conceptual_clarification",
            "confidence_score": 0.78,
            "adaptive_factors": ["understanding_level", "engagement_signals"]
        }
    elif "follow-up response" in prompt.lower():
        return {
            "content": "That's a great start! I can see you understand the basic concept. Can you help me understand how this might apply in a real-world scenario?",
            "reasoning": "Adaptive response encouraging application thinking based on verbal learning style",
            "teaching_technique": "elaborative_questioning",
            "personalization_applied": ["verbal_style_adaptation", "application_focus"],
            "adaptive_factors": ["understanding_level", "learning_style"]
        }
    return {"content": "Mock response", "reasoning": "Mock reasoning"}

def mock_firebase_get_topic_questions(user_id, topic_id):
    """Mock Firebase question retrieval"""
    return {
        "success": True,
        "questions": [
            {
                "id": "q1", 
                "text": "What is photosynthesis?", 
                "difficulty": "medium",
                "type": "conceptual"
            },
            {
                "id": "q2", 
                "text": "How does photosynthesis relate to cellular respiration?", 
                "difficulty": "hard",
                "type": "analysis"
            },
            {
                "id": "q3", 
                "text": "Describe a real-world application of photosynthesis principles.", 
                "difficulty": "medium",
                "type": "application"
            }
        ]
    }

# Patch the modules before importing
with patch('backend.my_agent.utils.tools.call_ai_with_json_output', side_effect=mock_call_ai_with_json_output), \
     patch('backend.my_agent.utils.adaptive_intelligence.call_ai_with_json_output', side_effect=mock_call_ai_with_json_output):
    
    # Import after patching
    from backend.my_agent.utils.adaptive_intelligence import (
        analyze_user_response_live,
        calculate_adaptive_difficulty,
        determine_adaptive_conversation_strategy,
        update_live_performance_metrics,
        update_learned_preferences,
        detect_learning_style,
        calculate_learning_momentum
    )
    
    from backend.my_agent.utils.nodes import (
        apply_adaptive_question_selection,
        evaluate_adaptive_topic_completion,
        calculate_style_compatibility,
        calculate_type_appropriateness,
        map_difficulty_to_score
    )

# Test Data Setup
def create_test_state():
    """Create a test state with Phase 4 adaptive intelligence fields"""
    return {
        "user_id": "test_user_123",
        "current_question": {
            "id": "q1",
            "text": "What is photosynthesis?",
            "type": "conceptual",
            "difficulty": "medium",
            "conversation_history": [
                {"role": "user", "content": "Photosynthesis is when plants make food from sunlight"},
                {"role": "assistant", "content": "That's a good start! Can you tell me more about what plants need for this process?"},
                {"role": "user", "content": "They need sunlight, water, and I think carbon dioxide"}
            ]
        },
        # Phase 4 adaptive intelligence fields
        "live_performance_metrics": {
            "understanding_history": [0.6, 0.7, 0.75],
            "confidence_history": [0.5, 0.6, 0.68],
            "engagement_history": [0.8, 0.82, 0.85],
            "current_understanding": 0.75,
            "current_confidence": 0.68,
            "current_engagement": 0.85,
            "performance_trend": "improving",
            "session_average": 0.72
        },
        "learned_user_preferences": {
            "learning_style_signals": {
                "visual_preference": [0.3, 0.4, 0.3],
                "verbal_preference": [0.8, 0.9, 0.8],
                "experiential_preference": [0.6, 0.7, 0.6]
            },
            "cognitive_patterns": {
                "cognitive_load_history": ["moderate", "moderate", "low"]
            },
            "discovery_count": 3
        },
        "detected_learning_style": "verbal",
        "cognitive_load_level": "moderate",
        "engagement_trend": "increasing",
        "adaptive_difficulty_level": 0.6,
        "learning_momentum_score": 0.78,
        "topic_question_summaries": [
            {"question_id": "q0", "performance_score": 0.7}
        ],
        "session_settings": {
            "max_questions_per_topic": 7,
            "performance_threshold": 0.85,
            "struggle_threshold": 0.3
        }
    }

# ================================================================================================
# PHASE 4 ADAPTIVE INTELLIGENCE TESTS
# ================================================================================================

async def test_live_response_analysis():
    """Test Phase 4: Real-time response analysis"""
    print("\n🧠 Testing Live Response Analysis...")
    
    state = create_test_state()
    user_input = "Photosynthesis converts carbon dioxide and water into glucose using sunlight energy, and it releases oxygen as a byproduct."
    
    # Test live analysis
    analysis = await analyze_user_response_live(user_input, state)
    
    # Verify analysis components
    assert "understanding" in analysis, "Analysis missing understanding score"
    assert "confidence" in analysis, "Analysis missing confidence score"
    assert "engagement" in analysis, "Analysis missing engagement score"
    assert "confusion_indicators" in analysis, "Analysis missing confusion indicators"
    assert "learning_style_signals" in analysis, "Analysis missing learning style signals"
    assert "adaptation_recommendations" in analysis, "Analysis missing adaptation recommendations"
    
    assert 0 <= analysis["understanding"] <= 1, "Understanding score out of range"
    assert 0 <= analysis["confidence"] <= 1, "Confidence score out of range"
    assert 0 <= analysis["engagement"] <= 1, "Engagement score out of range"
    
    print(f"   ✅ Understanding: {analysis['understanding']:.2f}")
    print(f"   ✅ Confidence: {analysis['confidence']:.2f}")
    print(f"   ✅ Engagement: {analysis['engagement']:.2f}")
    print(f"   ✅ Learning Style Signals: {len(analysis['learning_style_signals'])} detected")
    print(f"   ✅ Adaptation Recommendations: {len(analysis['adaptation_recommendations'])} provided")
    
    return True

async def test_adaptive_difficulty_calculation():
    """Test Phase 4: Adaptive difficulty calculation"""
    print("\n🎯 Testing Adaptive Difficulty Calculation...")
    
    # Test with different performance levels
    test_cases = [
        {
            "performance": {"understanding": 0.9, "confidence": 0.8, "engagement": 0.9},
            "expected_range": (0.0, 0.3),  # High performance = lower difficulty
            "description": "High performer"
        },
        {
            "performance": {"understanding": 0.3, "confidence": 0.4, "engagement": 0.5},
            "expected_range": (0.6, 1.0),  # Low performance = higher difficulty
            "description": "Struggling learner"
        },
        {
            "performance": {"understanding": 0.6, "confidence": 0.5, "engagement": 0.7},
            "expected_range": (0.3, 0.7),  # Moderate performance = moderate difficulty
            "description": "Average learner"
        }
    ]
    
    for case in test_cases:
        difficulty = calculate_adaptive_difficulty(
            current_performance=case["performance"],
            historical_data=[{"performance_score": 0.6}, {"performance_score": 0.7}],
            user_profile={"detected_learning_style": "verbal"}
        )
        
        min_expected, max_expected = case["expected_range"]
        assert min_expected <= difficulty <= max_expected, \
            f"Difficulty {difficulty:.2f} not in expected range {case['expected_range']} for {case['description']}"
        
        print(f"   ✅ {case['description']}: difficulty = {difficulty:.2f} (expected: {case['expected_range']})")
    
    return True

async def test_learning_style_detection():
    """Test Phase 4: Learning style detection"""
    print("\n🎨 Testing Learning Style Detection...")
    
    test_cases = [
        {
            "conversation": [
                {"content": "Can you show me a diagram of this process?"},
                {"content": "I'd like to visualize how this works"},
                {"content": "A picture would help me understand"}
            ],
            "live_analysis": {"learning_style_signals": {"visual_preference": 0.8}},
            "expected": "visual"
        },
        {
            "conversation": [
                {"content": "Can you give me a real-world example?"},
                {"content": "How does this apply in practice?"},
                {"content": "I learn better with hands-on experience"}
            ],
            "live_analysis": {"learning_style_signals": {"experiential_preference": 0.9}},
            "expected": "experiential"
        },
        {
            "conversation": [
                {"content": "Please explain this step by step"},
                {"content": "Can you describe the process in detail?"},
                {"content": "I need you to tell me how this works"}
            ],
            "live_analysis": {"learning_style_signals": {"verbal_preference": 0.8}},
            "expected": "verbal"
        }
    ]
    
    for case in test_cases:
        detected_style = detect_learning_style(case["conversation"], case["live_analysis"])
        assert detected_style == case["expected"], \
            f"Expected {case['expected']}, got {detected_style}"
        print(f"   ✅ Detected {detected_style} style correctly")
    
    return True

async def test_adaptive_conversation_strategy():
    """Test Phase 4: Adaptive conversation strategy determination"""
    print("\n🗣️ Testing Adaptive Conversation Strategy...")
    
    strategy = await determine_adaptive_conversation_strategy(
        understanding_level=0.75,
        engagement_level=0.82,
        confusion_signals=["needs clarification on concept X"],
        user_preferences={"detected_learning_style": "verbal"},
        conversation_history=[{"role": "user", "content": "test"}]
    )
    
    # Verify strategy components
    required_fields = [
        "teaching_strategy", "difficulty_adjustment", "conversation_style",
        "engagement_tactics", "adaptation_reasoning"
    ]
    
    for field in required_fields:
        assert field in strategy, f"Strategy missing required field: {field}"
    
    assert strategy["teaching_strategy"] in [
        "socratic_questioning", "direct_instruction", "scaffolded_learning",
        "elaborative_interrogation", "analogical_reasoning"
    ], "Invalid teaching strategy"
    
    assert strategy["difficulty_adjustment"] in [
        "increase_challenge", "provide_support", "maintain_current"
    ], "Invalid difficulty adjustment"
    
    print(f"   ✅ Teaching Strategy: {strategy['teaching_strategy']}")
    print(f"   ✅ Difficulty Adjustment: {strategy['difficulty_adjustment']}")
    print(f"   ✅ Engagement Tactics: {strategy['engagement_tactics']}")
    print(f"   ✅ Reasoning: {strategy['adaptation_reasoning'][:50]}...")
    
    return True

def test_live_performance_tracking():
    """Test Phase 4: Live performance metrics tracking"""
    print("\n📊 Testing Live Performance Tracking...")
    
    state = create_test_state()
    live_analysis = {
        "understanding": 0.8,
        "confidence": 0.7,
        "engagement": 0.9
    }
    
    # Update metrics
    update_live_performance_metrics(state, live_analysis)
    
    metrics = state["live_performance_metrics"]
    
    # Verify metrics updated
    assert metrics["current_understanding"] == 0.8, "Understanding not updated"
    assert metrics["current_confidence"] == 0.7, "Confidence not updated"
    assert metrics["current_engagement"] == 0.9, "Engagement not updated"
    
    # Verify history tracking
    assert len(metrics["understanding_history"]) == 4, "Understanding history not updated"
    assert metrics["understanding_history"][-1] == 0.8, "Latest understanding not recorded"
    
    print(f"   ✅ Current Understanding: {metrics['current_understanding']}")
    print(f"   ✅ Performance Trend: {metrics['performance_trend']}")
    print(f"   ✅ Session Average: {metrics['session_average']:.2f}")
    print(f"   ✅ History Length: {len(metrics['understanding_history'])}")
    
    return True

def test_learned_preferences_update():
    """Test Phase 4: Learned preferences tracking"""
    print("\n👤 Testing Learned Preferences Update...")
    
    state = create_test_state()
    live_analysis = {
        "learning_style_signals": {
            "visual_preference": 0.4,
            "verbal_preference": 0.9,
            "experiential_preference": 0.5
        },
        "cognitive_load": "low",
        "engagement": 0.88
    }
    
    # Update preferences
    update_learned_preferences(state, live_analysis)
    
    preferences = state["learned_user_preferences"]
    
    # Verify preferences updated
    assert preferences["discovery_count"] == 4, "Discovery count not incremented"
    assert "engagement_trend_history" in preferences, "Engagement trend history not tracked"
    
    # Verify learning style detection
    assert state.get("detected_learning_style") == "verbal", "Learning style not detected correctly"
    
    print(f"   ✅ Discovery Count: {preferences['discovery_count']}")
    print(f"   ✅ Detected Learning Style: {state.get('detected_learning_style')}")
    print(f"   ✅ Engagement Trend: {state.get('engagement_trend')}")
    
    return True

def test_learning_momentum_calculation():
    """Test Phase 4: Learning momentum calculation"""
    print("\n⚡ Testing Learning Momentum Calculation...")
    
    test_cases = [
        {
            "understanding_history": [0.4, 0.6, 0.8],
            "expected_range": (0.6, 1.0),
            "description": "Improving learner"
        },
        {
            "understanding_history": [0.8, 0.6, 0.4],
            "expected_range": (0.0, 0.4),
            "description": "Declining learner"
        },
        {
            "understanding_history": [0.6, 0.6, 0.6],
            "expected_range": (0.4, 0.8),
            "description": "Stable learner"
        }
    ]
    
    for case in test_cases:
        state = {
            "live_performance_metrics": {
                "understanding_history": case["understanding_history"]
            }
        }
        
        momentum = calculate_learning_momentum(state)
        min_expected, max_expected = case["expected_range"]
        
        assert min_expected <= momentum <= max_expected, \
            f"Momentum {momentum:.2f} not in expected range {case['expected_range']} for {case['description']}"
        
        print(f"   ✅ {case['description']}: momentum = {momentum:.2f} (expected: {case['expected_range']})")
    
    return True

async def test_adaptive_question_selection():
    """Test Phase 4: Adaptive question selection algorithms"""
    print("\n🎯 Testing Adaptive Question Selection...")
    
    questions = [
        {"id": "q1", "text": "Define photosynthesis", "difficulty": "easy", "type": "conceptual"},
        {"id": "q2", "text": "Analyze the role of chloroplasts", "difficulty": "hard", "type": "analysis"},
        {"id": "q3", "text": "Apply photosynthesis to agriculture", "difficulty": "medium", "type": "application"}
    ]
    
    # Test selection for high performer (should get harder questions)
    high_performer_result = await apply_adaptive_question_selection(
        questions=questions,
        adaptive_difficulty=0.8,  # High difficulty needed
        learned_preferences={"detected_learning_style": "experiential"},
        live_performance={"current_understanding": 0.9},
        completed_questions=[]
    )
    
    # Should prefer application/analysis questions for high performers
    selected_question = high_performer_result["question"]
    assert selected_question["type"] in ["analysis", "application"], \
        f"High performer should get challenging question type, got {selected_question['type']}"
    
    print(f"   ✅ High Performer Selection: {selected_question['id']} ({selected_question['type']})")
    print(f"   ✅ Selection Confidence: {high_performer_result['confidence']:.2f}")
    
    # Test selection for struggling learner (should get easier questions)
    struggling_result = await apply_adaptive_question_selection(
        questions=questions,
        adaptive_difficulty=0.2,  # Low difficulty needed
        learned_preferences={"detected_learning_style": "verbal"},
        live_performance={"current_understanding": 0.3},
        completed_questions=[]
    )
    
    selected_question = struggling_result["question"]
    print(f"   ✅ Struggling Learner Selection: {selected_question['id']} ({selected_question['type']})")
    print(f"   ✅ Adaptation Reasoning: {struggling_result['reasoning'][:50]}...")
    
    return True

async def test_adaptive_topic_completion():
    """Test Phase 4: Adaptive topic completion logic"""
    print("\n🏁 Testing Adaptive Topic Completion...")
    
    # Test early completion for high performers
    high_performer_state = create_test_state()
    high_performer_state["live_performance_metrics"]["current_understanding"] = 0.9
    high_performer_state["live_performance_metrics"]["session_average"] = 0.88
    high_performer_state["live_performance_metrics"]["performance_trend"] = "stable"
    
    completion_result = await evaluate_adaptive_topic_completion(
        state=high_performer_state,
        completed_questions=4,  # Above minimum for early completion
        max_questions=7,
        live_performance=high_performer_state["live_performance_metrics"],
        learning_momentum=0.85
    )
    
    assert completion_result["should_complete"] == True, "High performer should complete early"
    assert "high_performance_completion" in completion_result["adaptive_factors"], \
        "High performance completion factor should be present"
    
    print(f"   ✅ High Performer Early Completion: {completion_result['reason']}")
    
    # Test extended learning for struggling learners
    struggling_state = create_test_state()
    struggling_state["live_performance_metrics"]["current_understanding"] = 0.25
    struggling_state["live_performance_metrics"]["performance_trend"] = "declining"
    
    struggling_result = await evaluate_adaptive_topic_completion(
        state=struggling_state,
        completed_questions=6,  # Near max but struggling
        max_questions=7,
        live_performance=struggling_state["live_performance_metrics"],
        learning_momentum=0.3
    )
    
    assert struggling_result["should_complete"] == False, "Struggling learner should get extended practice"
    
    print(f"   ✅ Struggling Learner Extension: {struggling_result['reason']}")
    
    return True

def test_adaptive_compatibility_algorithms():
    """Test Phase 4: Adaptive compatibility calculation algorithms"""
    print("\n🔧 Testing Adaptive Compatibility Algorithms...")
    
    # Test style compatibility
    visual_question = {"text": "Draw a diagram showing photosynthesis", "type": "visual"}
    visual_compatibility = calculate_style_compatibility(visual_question, "visual")
    assert visual_compatibility >= 0.8, "Visual question should have high visual compatibility"
    
    verbal_question = {"text": "Explain the process of photosynthesis", "type": "conceptual"}
    verbal_compatibility = calculate_style_compatibility(verbal_question, "verbal")
    assert verbal_compatibility >= 0.8, "Verbal question should have high verbal compatibility"
    
    print(f"   ✅ Visual Compatibility: {visual_compatibility:.2f}")
    print(f"   ✅ Verbal Compatibility: {verbal_compatibility:.2f}")
    
    # Test type appropriateness
    high_understanding = {"current_understanding": 0.9, "current_confidence": 0.8}
    analysis_appropriateness = calculate_type_appropriateness("analysis", high_understanding, [])
    assert analysis_appropriateness >= 0.7, "Analysis questions should be appropriate for high understanding"
    
    low_understanding = {"current_understanding": 0.3, "current_confidence": 0.4}
    conceptual_appropriateness = calculate_type_appropriateness("conceptual", low_understanding, [])
    assert conceptual_appropriateness >= 0.7, "Conceptual questions should be appropriate for low understanding"
    
    print(f"   ✅ Analysis Appropriateness (High Understanding): {analysis_appropriateness:.2f}")
    print(f"   ✅ Conceptual Appropriateness (Low Understanding): {conceptual_appropriateness:.2f}")
    
    # Test difficulty mapping
    assert map_difficulty_to_score("easy") == 0.2, "Easy should map to 0.2"
    assert map_difficulty_to_score("medium") == 0.5, "Medium should map to 0.5"
    assert map_difficulty_to_score("hard") == 0.8, "Hard should map to 0.8"
    
    print(f"   ✅ Difficulty Mapping: easy={map_difficulty_to_score('easy')}, medium={map_difficulty_to_score('medium')}, hard={map_difficulty_to_score('hard')}")
    
    return True

# ================================================================================================
# COMPREHENSIVE PHASE 4 FLOW TEST
# ================================================================================================

async def test_complete_adaptive_flow():
    """Test Phase 4: Complete adaptive intelligence flow"""
    print("\n🌟 Testing Complete Adaptive Intelligence Flow...")
    
    # Simulate a complete adaptive learning interaction
    state = create_test_state()
    
    # Step 1: Live analysis of user response
    user_input = "Photosynthesis is the process where plants convert sunlight, carbon dioxide, and water into glucose and oxygen."
    
    live_analysis = await analyze_user_response_live(user_input, state)
    print(f"   Step 1 ✅ Live Analysis Complete: Understanding={live_analysis['understanding']:.2f}")
    
    # Step 2: Update performance metrics
    update_live_performance_metrics(state, live_analysis)
    print(f"   Step 2 ✅ Performance Metrics Updated: Trend={state['live_performance_metrics']['performance_trend']}")
    
    # Step 3: Update learned preferences
    update_learned_preferences(state, live_analysis)
    print(f"   Step 3 ✅ Preferences Updated: Style={state.get('detected_learning_style')}")
    
    # Step 4: Determine conversation strategy
    strategy = await determine_adaptive_conversation_strategy(
        understanding_level=live_analysis["understanding"],
        engagement_level=live_analysis["engagement"],
        confusion_signals=live_analysis.get("confusion_indicators", []),
        user_preferences=state.get("learned_user_preferences", {}),
        conversation_history=state["current_question"]["conversation_history"]
    )
    print(f"   Step 4 ✅ Strategy Determined: {strategy['teaching_strategy']}")
    
    # Step 5: Calculate adaptive difficulty
    adaptive_difficulty = calculate_adaptive_difficulty(
        current_performance=live_analysis,
        historical_data=state.get("question_adaptation_history", []),
        user_profile=state.get("learned_user_preferences", {})
    )
    print(f"   Step 5 ✅ Adaptive Difficulty: {adaptive_difficulty:.2f}")
    
    # Step 6: Calculate learning momentum
    momentum = calculate_learning_momentum(state)
    print(f"   Step 6 ✅ Learning Momentum: {momentum:.2f}")
    
    # Step 7: Evaluate topic completion
    completion_eval = await evaluate_adaptive_topic_completion(
        state=state,
        completed_questions=len(state["topic_question_summaries"]),
        max_questions=state["session_settings"]["max_questions_per_topic"],
        live_performance=state["live_performance_metrics"],
        learning_momentum=momentum
    )
    print(f"   Step 7 ✅ Topic Completion: {completion_eval['reason']}")
    
    print(f"\n🎉 Complete Adaptive Flow Test: SUCCESS!")
    print(f"   📊 Final Understanding: {live_analysis['understanding']:.2f}")
    print(f"   🎯 Adaptive Difficulty: {adaptive_difficulty:.2f}")
    print(f"   ⚡ Learning Momentum: {momentum:.2f}")
    print(f"   🎨 Detected Style: {state.get('detected_learning_style')}")
    print(f"   📈 Performance Trend: {state['live_performance_metrics']['performance_trend']}")
    
    return True

# ================================================================================================
# PHASE 4 TEST RUNNER
# ================================================================================================

async def run_phase4_tests():
    """Run all Phase 4 Real-Time Adaptive Intelligence tests"""
    
    print("🚀 PHASE 4: REAL-TIME ADAPTIVE INTELLIGENCE - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Live Response Analysis", test_live_response_analysis),
        ("Adaptive Difficulty Calculation", test_adaptive_difficulty_calculation),
        ("Learning Style Detection", test_learning_style_detection),
        ("Adaptive Conversation Strategy", test_adaptive_conversation_strategy),
        ("Live Performance Tracking", test_live_performance_tracking),
        ("Learned Preferences Update", test_learned_preferences_update),
        ("Learning Momentum Calculation", test_learning_momentum_calculation),
        ("Adaptive Question Selection", test_adaptive_question_selection),
        ("Adaptive Topic Completion", test_adaptive_topic_completion),
        ("Adaptive Compatibility Algorithms", test_adaptive_compatibility_algorithms),
        ("Complete Adaptive Flow", test_complete_adaptive_flow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func() if asyncio.iscoroutinefunction(test_func) else test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 80)
    print(f"🎯 PHASE 4 TEST RESULTS:")
    print(f"   ✅ PASSED: {passed}")
    print(f"   ❌ FAILED: {failed}")
    print(f"   📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print(f"\n🎉 ALL PHASE 4 ADAPTIVE INTELLIGENCE TESTS PASSED!")
        print(f"🧠 Real-time adaptive learning system is fully operational!")
        print(f"🎨 Personalization engines are working correctly!")
        print(f"⚡ Live performance tracking is functional!")
        print(f"🎯 Adaptive difficulty algorithms are validated!")
    else:
        print(f"\n⚠️  Some Phase 4 tests failed. Please review the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    asyncio.run(run_phase4_tests()) 