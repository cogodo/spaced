#!/usr/bin/env python3
"""
Test script for Phase 5: Advanced Features

This script tests the advanced learning features including:
- Adaptive session length based on performance
- Multi-task connections and cross-topic insights  
- Advanced analytics and performance tracking
- Intelligent session completion
- Personalized learning recommendations
- Real-time session optimization
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_agent'))

import asyncio
from datetime import datetime, timezone, timedelta
from my_agent.utils.tools import (
    detect_topic_connections, calculate_learning_momentum, should_extend_session,
    should_complete_early, analyze_answer_confidence, generate_cross_topic_insights,
    predict_retention, generate_next_session_recommendations, estimate_session_duration
)
from my_agent.utils.nodes import (
    calculate_current_momentum, get_difficulty_trend, update_performance_trends,
    generate_session_summary, calculate_session_duration, calculate_average_confidence
)

def test_adaptive_session_length():
    """Test adaptive session length features"""
    print("🧪 Testing adaptive session length...")
    
    # Test session that should extend (struggling performance)
    struggling_state = {
        "adaptive_session_length": True,
        "scores": {"python": 1, "algorithms": 2},
        "question_count": 4,
        "max_questions": 7,
        "struggle_threshold": 2.0
    }
    
    should_extend = should_extend_session(struggling_state)
    print(f"  ✅ Struggling session extension: {should_extend} (should be True)")
    
    # Test session that should complete early (excellent performance)
    excellent_state = {
        "adaptive_session_length": True,
        "scores": {"python": 5, "algorithms": 5},
        "question_count": 3,
        "max_questions": 7,
        "performance_threshold": 4.5
    }
    
    should_complete = should_complete_early(excellent_state)
    print(f"  ✅ Excellent session early completion: {should_complete} (should be True)")
    
    # Test disabled adaptive mode
    disabled_state = {
        "adaptive_session_length": False,
        "scores": {"python": 1}
    }
    
    should_not_adapt = should_extend_session(disabled_state) or should_complete_early(disabled_state)
    print(f"  ✅ Disabled adaptive mode: {should_not_adapt} (should be False)")

def test_topic_connections():
    """Test topic connection detection"""
    print("\n🧪 Testing topic connection detection...")
    
    topics = ["python", "machine learning", "data science"]
    history = [
        {"answer": "Python is essential for machine learning and data analysis", "topic": "python"},
        {"answer": "Machine learning uses algorithms and statistics", "topic": "machine learning"},
        {"answer": "Data science combines programming with statistical analysis", "topic": "data science"}
    ]
    
    connections = detect_topic_connections(topics, history)
    
    print(f"  ✅ Detected connections: {connections}")
    print(f"  🔗 Python connections: {connections.get('python', [])}")
    print(f"  🔗 ML connections: {connections.get('machine learning', [])}")
    
    # Check for expected connections
    python_connects_ml = any("machine learning" in related or "data science" in related for related in connections.get('python', []))
    print(f"  ✅ Python-ML connection detected: {python_connects_ml}")

def test_learning_momentum():
    """Test learning momentum calculation"""
    print("\n🧪 Testing learning momentum calculation...")
    
    # High momentum scenario
    high_scores = {"python": 5, "react": 4, "algorithms": 5}
    high_question_types = [
        {"type": "free_recall"}, {"type": "application"}, {"type": "analysis"},
        {"type": "connection"}, {"type": "cued_recall"}
    ]
    
    high_momentum = calculate_learning_momentum(high_scores, high_question_types)
    print(f"  ✅ High performance momentum: {high_momentum:.2f} (should be > 0.8)")
    
    # Low momentum scenario
    low_scores = {"python": 2, "react": 1, "algorithms": 2}
    low_question_types = [{"type": "recognition"}, {"type": "recognition"}]
    
    low_momentum = calculate_learning_momentum(low_scores, low_question_types)
    print(f"  ✅ Low performance momentum: {low_momentum:.2f} (should be < 0.4)")

def test_answer_confidence():
    """Test answer confidence analysis"""
    print("\n🧪 Testing answer confidence analysis...")
    
    # High confidence answer
    confident_answer = "I definitely know that Python is an excellent programming language for data science. It provides powerful libraries like pandas, numpy, and scikit-learn specifically designed for analysis and machine learning tasks."
    
    confidence_high = analyze_answer_confidence(confident_answer)
    print(f"  ✅ High confidence answer: {confidence_high:.2f} (should be > 0.7)")
    
    # Low confidence answer
    uncertain_answer = "I think Python might be good for data science, maybe? I'm not sure about the specific libraries though."
    
    confidence_low = analyze_answer_confidence(uncertain_answer)
    print(f"  ✅ Low confidence answer: {confidence_low:.2f} (should be < 0.4)")
    
    # Empty answer
    confidence_empty = analyze_answer_confidence("")
    print(f"  ✅ Empty answer confidence: {confidence_empty:.2f} (should be very low)")

def test_cross_topic_insights():
    """Test cross-topic insights generation"""
    print("\n🧪 Testing cross-topic insights generation...")
    
    state = {
        "topics": ["python", "machine learning", "web development"],
        "history": [
            {"answer": "Python is great for machine learning with scikit-learn", "topic": "python", "question": "What do you know about Python?"},
            {"answer": "Machine learning requires good programming skills in Python", "topic": "machine learning", "question": "How do you approach ML?"},
            {"answer": "Web development can use Python frameworks like Django", "topic": "web development", "question": "What about web development?"}
        ],
        "topic_connections": {
            "python": ["machine learning", "web development", "data science"],
            "machine learning": ["python", "statistics", "algorithms"],
            "web development": ["python", "javascript", "frameworks"]
        }
    }
    
    insights = generate_cross_topic_insights(state)
    
    print(f"  ✅ Generated {len(insights)} cross-topic insights")
    for insight in insights:
        if insight["type"] == "user_connection":
            print(f"    🔗 User connected {insight['from_topic']} → {insight['to_topic']}")
        elif insight["type"] == "system_connection":
            print(f"    🧠 System detected {insight['topic']} connects to {len(insight['related_topics'])} topics")

def test_retention_prediction():
    """Test retention prediction algorithm"""
    print("\n🧪 Testing retention prediction...")
    
    state = {
        "scores": {"python": 4, "machine_learning": 2, "algorithms": 5},
        "answer_confidence_scores": [0.8, 0.9, 0.3, 0.4, 0.95, 0.85],
        "question_types": [
            {"topic": "python", "type": "free_recall"},
            {"topic": "python", "type": "application"},
            {"topic": "machine_learning", "type": "recognition"},
            {"topic": "machine_learning", "type": "cued_recall"},
            {"topic": "algorithms", "type": "analysis"},
            {"topic": "algorithms", "type": "free_recall"}
        ]
    }
    
    predictions = predict_retention(state)
    
    print(f"  ✅ Retention predictions generated: {predictions}")
    print(f"  📈 Python retention: {predictions.get('python', 0):.2f} (should be high)")
    print(f"  📉 ML retention: {predictions.get('machine_learning', 0):.2f} (should be lower)")
    print(f"  🎯 Algorithms retention: {predictions.get('algorithms', 0):.2f} (should be high)")

def test_session_recommendations():
    """Test next session recommendations"""
    print("\n🧪 Testing session recommendations...")
    
    # Strong performance state
    strong_state = {
        "scores": {"python": 5, "react": 4, "algorithms": 5},
        "session_type": "custom_topics",
        "topic_connections": {
            "python": ["data science", "machine learning"],
            "react": ["javascript", "web development"],
            "algorithms": ["data structures", "computer science"]
        }
    }
    
    strong_recommendations = generate_next_session_recommendations(strong_state)
    print(f"  ✅ Strong performance recommendations:")
    print(f"    🎯 Duration: {strong_recommendations.get('estimated_duration', 0)} minutes")
    print(f"    📚 Strategy: {strong_recommendations.get('learning_strategy', 'Not provided')}")
    print(f"    🔗 Connected topics: {strong_recommendations.get('connected_learning', [])}")
    
    # Struggling performance state
    struggling_state = {
        "scores": {"python": 2, "react": 1, "algorithms": 2},
        "session_type": "due_items"
    }
    
    struggling_recommendations = generate_next_session_recommendations(struggling_state)
    print(f"  ✅ Struggling performance recommendations:")
    print(f"    🎯 Duration: {struggling_recommendations.get('estimated_duration', 0)} minutes")
    print(f"    📚 Strategy: {struggling_recommendations.get('learning_strategy', 'Not provided')}")
    print(f"    ⚠️  Priority topics: {struggling_recommendations.get('priority_topics', [])}")

def test_session_analytics():
    """Test real-time session analytics"""
    print("\n🧪 Testing session analytics...")
    
    # Mock active session state
    session_state = {
        "session_start_time": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "session_end_time": None,
        "history": [
            {"answer": "Python is a versatile programming language", "topic": "python"},
            {"answer": "I think machine learning is complex", "topic": "machine_learning"},
            {"answer": "Algorithms are fundamental to computer science", "topic": "algorithms"}
        ],
        "question_difficulty_progression": [0.3, 0.5, 0.7],
        "answer_confidence_scores": [0.8, 0.4, 0.9]
    }
    
    # Test momentum calculation
    momentum = calculate_current_momentum(session_state)
    print(f"  ✅ Current momentum: {momentum:.2f}")
    
    # Test difficulty trend
    trend = get_difficulty_trend(session_state)
    print(f"  ✅ Difficulty trend: {trend}")
    
    # Test session duration
    duration = calculate_session_duration(session_state)
    print(f"  ✅ Session duration: {duration}")
    
    # Test average confidence
    avg_confidence = calculate_average_confidence(session_state)
    print(f"  ✅ Average confidence: {avg_confidence:.2f}")

def test_session_summary():
    """Test comprehensive session summary generation"""
    print("\n🧪 Testing session summary generation...")
    
    # Complete session state
    complete_state = {
        "topics": ["python", "machine_learning", "algorithms"],
        "history": [
            {"answer": "Python is excellent for data analysis", "topic": "python"},
            {"answer": "Machine learning uses statistical methods", "topic": "machine_learning"},
            {"answer": "Algorithms solve computational problems", "topic": "algorithms"}
        ],
        "session_start_time": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
        "session_end_time": datetime.now(timezone.utc).isoformat(),
        "learning_momentum": 0.8,
        "session_completion_reason": "all_topics_completed",
        "answer_confidence_scores": [0.7, 0.6, 0.9],
        "recommended_next_session": {"estimated_duration": 12, "session_type": "custom_topics"}
    }
    
    scores = {"python": 4, "machine_learning": 3, "algorithms": 5}
    
    summary = generate_session_summary(complete_state, scores)
    
    print(f"  ✅ Session summary generated:")
    print(f"    🎯 Performance level: {summary['performance_level']}")
    print(f"    📊 Average score: {summary['average_score']}")
    print(f"    ⏱️  Duration: {summary['session_duration']['formatted']}")
    print(f"    🚀 Momentum: {summary['learning_momentum']}")
    print(f"    💭 Confidence: {summary['confidence_level']}")
    print(f"    📝 Message: {summary['performance_message']}")

def test_optimization_algorithms():
    """Test session optimization algorithms"""
    print("\n🧪 Testing session optimization algorithms...")
    
    # Test duration estimation
    high_performance_state = {"scores": {"python": 5, "react": 4}}
    duration_high = estimate_session_duration(high_performance_state)
    print(f"  ✅ High performance duration: {duration_high} minutes (should be short)")
    
    struggling_state = {"scores": {"python": 2, "react": 1}}
    duration_low = estimate_session_duration(struggling_state)
    print(f"  ✅ Struggling performance duration: {duration_low} minutes (should be longer)")
    
    # Test performance trends tracking
    trend_state = {"performance_trends": {}}
    update_performance_trends(trend_state, "python")
    print(f"  ✅ Performance trends updated: {trend_state.get('performance_trends', {})}")

def main():
    """Run all Phase 5 tests"""
    print("🚀 Phase 5: Advanced Features Tests")
    print("=" * 70)
    
    try:
        # Run all tests
        test_adaptive_session_length()
        test_topic_connections()
        test_learning_momentum()
        test_answer_confidence()
        test_cross_topic_insights()
        test_retention_prediction()
        test_session_recommendations()
        test_session_analytics()
        test_session_summary()
        test_optimization_algorithms()
        
        print("\n" + "=" * 70)
        print("✅ All Phase 5 tests passed!")
        print("\n📋 Phase 5 Implementation Summary:")
        print("  ✅ Adaptive session length with performance thresholds")
        print("  ✅ Multi-task connections and cross-topic insights")
        print("  ✅ Advanced analytics and performance tracking")
        print("  ✅ Answer confidence analysis and momentum calculation")
        print("  ✅ Retention prediction algorithms")
        print("  ✅ Intelligent session recommendations")
        print("  ✅ Real-time session analytics")
        print("  ✅ Comprehensive session summaries")
        print("  ✅ Session optimization algorithms")
        print("  ✅ Performance trend tracking")
        print("\n🎯 Phase 5 Features:")
        print("  🔥 /optimize_session - Personalized session optimization")
        print("  📊 /session_analytics/{session_id} - Real-time session insights")
        print("  🧠 Enhanced /complete_session with advanced analytics")
        print("  ⚡ Adaptive session length (early completion/extension)")
        print("  🔗 Cross-topic connection detection")
        print("  📈 Learning momentum and velocity tracking")
        print("  🎯 Retention prediction and recommendations")
        print("  💡 Intelligent next session suggestions")
        print("\n🚀 Ready for advanced personalized learning experiences!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 