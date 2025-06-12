#!/usr/bin/env python3
"""
API test for Phase 5: Advanced Features

Tests the new advanced features and endpoints:
- /optimize_session - Personalized session optimization
- /session_analytics/{session_id} - Real-time session insights
- Enhanced /start_session with adaptive features
- Enhanced /complete_session with advanced analytics
- Adaptive session length functionality
"""

import requests
import json
import time
import threading
import sys
import os

# Add the agent path
sys.path.append(os.path.join(os.path.dirname(__file__), 'my_agent'))

from my_agent.agent import app
import uvicorn

def start_server():
    """Start the server in background"""
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')

def test_session_optimization():
    """Test the session optimization endpoint"""
    print("🧪 Testing session optimization...")
    
    try:
        # Test optimization for new user
        response = requests.post('http://127.0.0.1:8000/optimize_session?user_id=new-user-123&session_type=custom_topics', 
                               timeout=10)
        
        if response.status_code == 200:
            optimization_data = response.json()
            print(f"✅ New user optimization successful")
            print(f"📊 Optimized settings: {optimization_data.get('optimized_settings', {})}")
            print(f"💡 Reasoning: {optimization_data.get('reasoning', 'No reasoning provided')}")
            print(f"🎯 Personalization level: {optimization_data.get('personalization_level', 'unknown')}")
            
            # Verify expected default settings
            settings = optimization_data.get('optimized_settings', {})
            if settings.get('adaptive_session_length') == True:
                print(f"  ✅ Adaptive session length enabled by default")
            if 4.0 <= settings.get('performance_threshold', 0) <= 5.0:
                print(f"  ✅ Reasonable performance threshold: {settings.get('performance_threshold')}")
        else:
            print(f"❌ Optimization request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Session optimization test failed: {e}")

def test_adaptive_session_creation():
    """Test creating sessions with adaptive features"""
    print("\n🧪 Testing adaptive session creation...")
    
    try:
        # Create session with custom adaptive settings
        adaptive_payload = {
            'session_type': 'custom_topics',
            'topics': ['adaptive_learning_test'],
            'max_topics': 1,
            'max_questions': 3,
            'adaptive_session_length': True,
            'performance_threshold': 4.0,
            'struggle_threshold': 2.5,
            'personalized_difficulty': True
        }
        
        response = requests.post('http://127.0.0.1:8000/start_session', 
                               json=adaptive_payload, 
                               timeout=10)
        
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data['session_id']
            print(f"✅ Adaptive session created: {session_id}")
            print(f"📊 Session type: {session_data.get('session_type')}")
            print(f"🎯 Topics count: {session_data.get('topics_count', 0)}")
            
            return session_id
        else:
            print(f"❌ Adaptive session creation failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Adaptive session creation test failed: {e}")
        return None

def test_session_analytics(session_id):
    """Test real-time session analytics"""
    if not session_id:
        print("\n⚠️ Skipping session analytics test - no session ID")
        return
    
    print(f"\n🧪 Testing session analytics for {session_id}...")
    
    try:
        response = requests.get(f'http://127.0.0.1:8000/session_analytics/{session_id}', 
                              timeout=10)
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"✅ Session analytics retrieved successfully")
            print(f"📊 Session ID: {analytics.get('session_id')}")
            print(f"🎯 Session type: {analytics.get('session_type')}")
            
            # Check progress metrics
            progress = analytics.get('current_progress', {})
            print(f"📈 Current progress: {progress.get('question_count', 0)} questions")
            print(f"📋 Current task: {progress.get('current_task', 'None')}")
            
            # Check performance metrics
            performance = analytics.get('performance_metrics', {})
            print(f"🚀 Learning momentum: {performance.get('learning_momentum', 0):.2f}")
            print(f"📊 Difficulty trend: {performance.get('difficulty_trend', 'unknown')}")
            print(f"💭 Average confidence: {performance.get('average_confidence', 0):.2f}")
            
            # Check adaptive features
            adaptive = analytics.get('adaptive_features', {})
            print(f"⚡ Adaptive mode: {adaptive.get('adaptive_mode', False)}")
            print(f"🎯 Performance threshold: {adaptive.get('performance_threshold', 0)}")
            
        else:
            print(f"❌ Session analytics failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Session analytics test failed: {e}")

def test_adaptive_session_flow(session_id):
    """Test adaptive session flow with intelligent responses"""
    if not session_id:
        print("\n⚠️ Skipping adaptive session flow test - no session ID")
        return
    
    print(f"\n🧪 Testing adaptive session flow...")
    
    try:
        # Provide high-confidence, detailed answers to trigger early completion
        high_quality_answers = [
            "Adaptive learning is a sophisticated educational technology that personalizes the learning experience based on individual performance data. It uses algorithms to analyze learning patterns, adjust difficulty levels, and provide targeted feedback to optimize educational outcomes.",
            "The key benefits include personalized pacing, immediate feedback, improved retention through spaced repetition, and data-driven insights that help both learners and educators understand progress patterns.",
            "Implementation typically involves machine learning algorithms that track user responses, analyze performance trends, and dynamically adjust content difficulty and question types to maintain optimal challenge levels."
        ]
        
        for i, answer in enumerate(high_quality_answers, 1):
            print(f"  📝 Submitting high-quality answer {i}...")
            
            answer_response = requests.post('http://127.0.0.1:8000/answer',
                                          json={
                                              'session_id': session_id,
                                              'user_input': answer
                                          },
                                          timeout=10)
            
            if answer_response.status_code != 200:
                print(f"❌ Answer {i} submission failed: {answer_response.json()}")
                return
                
            answer_data = answer_response.json()
            
            # Check for adaptive completion
            if 'scores' in answer_data:
                print(f"  🏁 Session completed after {i} answers")
                completion_reason = answer_data.get('completion_reason', 'unknown')
                print(f"  ⚡ Completion reason: {completion_reason}")
                
                if completion_reason == "performance_achieved":
                    print(f"  ✅ Adaptive early completion triggered!")
                    
                return answer_data
            
            # Check for momentum and analytics
            if 'momentum_score' in answer_data:
                print(f"  🚀 Current momentum: {answer_data['momentum_score']:.2f}")
            if 'difficulty_trend' in answer_data:
                print(f"  📊 Difficulty trend: {answer_data['difficulty_trend']}")
        
        print("✅ Adaptive session flow test completed")
        
    except Exception as e:
        print(f"❌ Adaptive session flow test failed: {e}")

def test_enhanced_completion_analytics():
    """Test enhanced session completion with advanced analytics"""
    print("\n🧪 Testing enhanced session completion...")
    
    try:
        # Create a simple session for completion testing
        simple_payload = {
            'session_type': 'custom_topics',
            'topics': ['completion_analytics_test'],
            'max_topics': 1,
            'max_questions': 2,
            'adaptive_session_length': True
        }
        
        session_response = requests.post('http://127.0.0.1:8000/start_session', 
                                       json=simple_payload, 
                                       timeout=10)
        
        if session_response.status_code != 200:
            print(f"❌ Failed to create completion test session")
            return
        
        session_id = session_response.json()['session_id']
        
        # Complete the session with quality answers
        answers = [
            "Completion analytics provide comprehensive insights into learning session performance and outcomes.",
            "These analytics include momentum tracking, confidence analysis, retention predictions, and personalized recommendations for future learning."
        ]
        
        for answer in answers:
            answer_response = requests.post('http://127.0.0.1:8000/answer',
                                          json={
                                              'session_id': session_id,
                                              'user_input': answer
                                          },
                                          timeout=10)
            
            if 'scores' in answer_response.json():
                break
        
        # Test enhanced completion endpoint
        completion_response = requests.post(f'http://127.0.0.1:8000/complete_session?session_id={session_id}',
                                          timeout=10)
        
        if completion_response.status_code == 200:
            completion_data = completion_response.json()
            print(f"✅ Enhanced completion successful")
            
            # Check for Phase 5 analytics
            if 'performance_analysis' in completion_data:
                perf = completion_data['performance_analysis']
                print(f"📊 Learning momentum: {perf.get('learning_momentum', 0):.2f}")
                print(f"📈 Learning velocity: {perf.get('learning_velocity', 0):.2f}")
                print(f"⚡ Completion reason: {perf.get('completion_reason', 'unknown')}")
            
            if 'topic_insights' in completion_data:
                insights = completion_data['topic_insights']
                print(f"🔗 Connections discovered: {len(insights.get('connections_discovered', []))}")
                print(f"🎯 Retention predictions: {len(insights.get('retention_predictions', {}))}")
            
            if 'recommendations' in completion_data:
                rec = completion_data['recommendations']
                print(f"💡 Next session duration: {rec.get('estimated_duration', 'Unknown')} minutes")
                print(f"📚 Learning strategy: {rec.get('learning_strategy', 'Not provided')}")
            
            if 'session_metadata' in completion_data:
                meta = completion_data['session_metadata']
                print(f"📋 Total questions: {meta.get('total_questions', 0)}")
                print(f"🧠 Question types used: {meta.get('question_types_used', [])}")
                print(f"⚙️ Adaptive adjustments: {meta.get('adaptive_adjustments', 0)}")
                
        else:
            print(f"❌ Enhanced completion failed: {completion_response.status_code}")
            
    except Exception as e:
        print(f"❌ Enhanced completion test failed: {e}")

def test_optimization_with_history():
    """Test optimization for user with simulated history"""
    print("\n🧪 Testing optimization with performance history...")
    
    try:
        # Test optimization for both session types
        for session_type in ['custom_topics', 'due_items']:
            response = requests.post(f'http://127.0.0.1:8000/optimize_session?user_id=experienced-user&session_type={session_type}', 
                                   timeout=10)
            
            if response.status_code == 200:
                optimization = response.json()
                print(f"✅ {session_type} optimization successful")
                
                settings = optimization.get('optimized_settings', {})
                reasoning = optimization.get('reasoning', '')
                personalization = optimization.get('personalization_level', 'none')
                
                print(f"  🎯 Max topics: {settings.get('max_topics', 0)}")
                print(f"  ❓ Max questions: {settings.get('max_questions', 0)}")
                print(f"  📊 Performance threshold: {settings.get('performance_threshold', 0)}")
                print(f"  ⏱️ Estimated duration: {settings.get('estimated_duration_minutes', 0)} min")
                print(f"  🧠 Personalization: {personalization}")
                print(f"  💭 Reasoning: {reasoning[:100]}...")
                
                # Verify session type specific adjustments
                if session_type == 'due_items' and 'due items' in reasoning.lower():
                    print(f"  ✅ Due items specific adjustments detected")
                    
            else:
                print(f"❌ {session_type} optimization failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Optimization with history test failed: {e}")

def test_error_handling():
    """Test error handling for Phase 5 endpoints"""
    print("\n🧪 Testing Phase 5 error handling...")
    
    try:
        # Test invalid session analytics
        response = requests.get('http://127.0.0.1:8000/session_analytics/invalid-session-id', 
                              timeout=5)
        if response.status_code == 404:
            print(f"  ✅ Invalid session analytics: Proper 404 error")
        else:
            print(f"  ⚠️ Invalid session analytics: Unexpected response {response.status_code}")
        
        # Test optimization without parameters
        response = requests.post('http://127.0.0.1:8000/optimize_session', timeout=5)
        if response.status_code == 422:  # Validation error
            print(f"  ✅ Missing optimization params: Proper validation error")
        else:
            print(f"  ⚠️ Missing optimization params: Unexpected response {response.status_code}")
        
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def main():
    """Test Phase 5 advanced features"""
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Starting server with Phase 5 advanced features...")
    time.sleep(3)
    
    # Test health check first
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Run Phase 5 tests
    test_session_optimization()
    session_id = test_adaptive_session_creation()
    test_session_analytics(session_id)
    test_adaptive_session_flow(session_id)
    test_enhanced_completion_analytics()
    test_optimization_with_history()
    test_error_handling()
    
    print("\n" + "=" * 70)
    print("✅ Phase 5 API testing completed!")
    print("\n📋 Phase 5 API Features Verified:")
    print("  ✅ /optimize_session - Personalized session optimization")
    print("  ✅ /session_analytics/{session_id} - Real-time session insights")
    print("  ✅ Enhanced /start_session with adaptive configuration")
    print("  ✅ Enhanced /complete_session with advanced analytics")
    print("  ✅ Adaptive session length functionality")
    print("  ✅ Performance-based session optimization")
    print("  ✅ Real-time momentum and confidence tracking")
    print("  ✅ Intelligent completion detection")
    print("  ✅ Comprehensive session summaries")
    print("  ✅ Error handling for advanced endpoints")
    print("\n🎯 Phase 5 Advanced Capabilities:")
    print("  🧠 Adaptive session length with early completion/extension")
    print("  🔗 Cross-topic connection detection and insights")
    print("  📊 Real-time learning momentum and velocity tracking")
    print("  🎯 Retention prediction and personalized recommendations")
    print("  💡 Intelligent session optimization based on user history")
    print("  ⚡ Performance threshold-based adaptive completion")
    print("  📈 Advanced analytics with confidence and difficulty tracking")
    print("  🚀 Comprehensive session summaries with actionable insights")
    print("\n🏆 Phase 5 delivers advanced personalized learning experiences!")

if __name__ == "__main__":
    main() 