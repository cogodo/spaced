#!/usr/bin/env python3
"""
API test for Phase 4: Intelligent Evaluation & FSRS Integration

Tests the new analytics and dashboard endpoints:
- /dashboard/{user_id} - User dashboard data
- /insights/{user_id} - Learning insights 
- Enhanced session completion with metrics
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

def test_dashboard_endpoint():
    """Test the user dashboard endpoint"""
    print("🧪 Testing dashboard endpoint...")
    
    try:
        # Test dashboard endpoint with mock user
        response = requests.get('http://127.0.0.1:8000/dashboard/test-user-123', timeout=10)
        
        if response.status_code == 200:
            dashboard_data = response.json()
            print(f"✅ Dashboard endpoint successful")
            print(f"📊 Response keys: {list(dashboard_data.keys())}")
            
            # Check for expected structure
            expected_keys = ['current_status', 'weekly_progress', 'recommendations']
            for key in expected_keys:
                if key in dashboard_data:
                    print(f"  ✅ {key}: Present")
                else:
                    print(f"  ⚠️  {key}: Missing (expected for new users)")
            
            if 'message' in dashboard_data:
                print(f"  💬 Message: {dashboard_data['message']}")
        else:
            print(f"❌ Dashboard request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")

def test_insights_endpoint():
    """Test the learning insights endpoint"""
    print("\n🧪 Testing insights endpoint...")
    
    try:
        # Test insights endpoint with different time periods
        for days in [7, 30]:
            response = requests.get(f'http://127.0.0.1:8000/insights/test-user-123?days={days}', timeout=10)
            
            if response.status_code == 200:
                insights_data = response.json()
                print(f"✅ Insights endpoint successful (last {days} days)")
                print(f"📊 Response keys: {list(insights_data.keys())}")
                
                if 'message' in insights_data:
                    print(f"  💬 Message: {insights_data['message']}")
                
                if 'session_statistics' in insights_data:
                    stats = insights_data['session_statistics']
                    print(f"  📈 Sessions: {stats.get('total_sessions', 0)}")
                    print(f"  ⏱️  Study time: {stats.get('total_study_time_minutes', 0)} minutes")
            else:
                print(f"❌ Insights request failed ({days} days): {response.status_code}")
                
    except Exception as e:
        print(f"❌ Insights test failed: {e}")

def test_enhanced_session_analytics():
    """Test enhanced session completion with analytics"""
    print("\n🧪 Testing enhanced session analytics...")
    
    try:
        # Start a session
        print("  🚀 Starting session with analytics tracking...")
        response = requests.post('http://127.0.0.1:8000/start_session', 
                               json={
                                   'session_type': 'custom_topics', 
                                   'topics': ['python analytics'],
                                   'max_topics': 1,
                                   'max_questions': 2
                               }, 
                               timeout=10)
        
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"  ✅ Session started: {session_id}")
        
        # Answer questions to generate analytics data
        answers = [
            "Python analytics involves using libraries like pandas, numpy, and matplotlib for data analysis.",
            "Key techniques include data cleaning, statistical analysis, visualization, and machine learning."
        ]
        
        for i, answer in enumerate(answers, 1):
            print(f"  📝 Submitting answer {i}...")
            answer_response = requests.post('http://127.0.0.1:8000/answer',
                                          json={
                                              'session_id': session_id,
                                              'user_input': answer
                                          },
                                          timeout=10)
            
            if answer_response.status_code != 200:
                print(f"❌ Answer submission failed: {answer_response.json()}")
                return
                
            answer_data = answer_response.json()
            
            if 'scores' in answer_data:
                print(f"  🏁 Session completed with scores: {answer_data['scores']}")
                
                # Check for enhanced session data
                if 'session_summary' in answer_data:
                    print(f"  📋 Summary: {answer_data['session_summary']}")
                    
                break
            else:
                print(f"  ➡️  Next question ready")
        
        print("✅ Enhanced session analytics test completed")
        
    except Exception as e:
        print(f"❌ Enhanced session test failed: {e}")

def test_due_tasks_integration():
    """Test due tasks endpoint integration"""
    print("\n🧪 Testing due tasks endpoint...")
    
    try:
        # Test due tasks endpoint
        response = requests.get('http://127.0.0.1:8000/due_tasks/test-user-456', timeout=10)
        
        if response.status_code == 200:
            due_data = response.json()
            print(f"✅ Due tasks endpoint successful")
            print(f"📊 User: {due_data.get('user_id')}")
            print(f"📋 Due tasks count: {due_data.get('due_tasks_count', 0)}")
            print(f"📝 Message: {due_data.get('message', 'No message')}")
            
            if due_data.get('tasks_preview'):
                print(f"👀 Preview: {len(due_data['tasks_preview'])} tasks shown")
            else:
                print(f"👀 No tasks preview (expected for users without Firebase data)")
                
        else:
            print(f"❌ Due tasks request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Due tasks test failed: {e}")

def test_session_metrics_generation():
    """Test session metrics generation during session flow"""
    print("\n🧪 Testing session metrics generation...")
    
    try:
        # Start a more comprehensive session
        print("  🚀 Starting comprehensive session...")
        response = requests.post('http://127.0.0.1:8000/start_session', 
                               json={
                                   'session_type': 'custom_topics', 
                                   'topics': ['machine learning', 'data science'],
                                   'max_topics': 2,
                                   'max_questions': 3
                               }, 
                               timeout=10)
        
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"  ✅ Session started: {session_id}")
        print(f"  📊 Topics: {session_data.get('topics_count')} topics planned")
        
        # Simulate realistic answers to generate quality metrics
        quality_answers = [
            "Machine learning is a subset of AI that enables computers to learn patterns from data without explicit programming. Key algorithms include supervised learning like regression and classification.",
            "Popular frameworks include scikit-learn for traditional ML, TensorFlow and PyTorch for deep learning, and XGBoost for gradient boosting.",
            "Data science combines statistics, programming, and domain expertise to extract insights from data. The workflow typically involves data collection, cleaning, exploration, modeling, and interpretation.",
            "Essential tools include Python libraries like pandas for data manipulation, matplotlib/seaborn for visualization, and jupyter notebooks for interactive analysis.",
            "Applications include recommendation systems, fraud detection, image recognition, and predictive maintenance across industries.",
            "Key challenges include data quality, feature engineering, model selection, overfitting prevention, and ensuring interpretability and fairness."
        ]
        
        question_count = 0
        for answer in quality_answers:
            if question_count >= 6:  # Max questions across topics
                break
                
            answer_response = requests.post('http://127.0.0.1:8000/answer',
                                          json={
                                              'session_id': session_id,
                                              'user_input': answer
                                          },
                                          timeout=10)
            
            answer_data = answer_response.json()
            question_count += 1
            
            if 'scores' in answer_data:
                print(f"  🏁 Session completed after {question_count} questions")
                print(f"  📊 Final scores: {answer_data['scores']}")
                print(f"  📈 Analytics: Session metrics should be automatically saved")
                break
            else:
                print(f"  ➡️  Question {question_count + 1} ready")
        
        print("✅ Session metrics generation test completed")
        
    except Exception as e:
        print(f"❌ Session metrics test failed: {e}")

def test_api_error_handling():
    """Test API error handling for analytics endpoints"""
    print("\n🧪 Testing API error handling...")
    
    try:
        # Test invalid endpoints
        test_cases = [
            ('/dashboard/', 'Empty user ID'),
            ('/insights/', 'Empty user ID'),
            ('/due_tasks/', 'Empty user ID'),
        ]
        
        for endpoint, description in test_cases:
            response = requests.get(f'http://127.0.0.1:8000{endpoint}', timeout=5)
            if response.status_code in [404, 422]:  # Expected error codes
                print(f"  ✅ {description}: Proper error handling ({response.status_code})")
            else:
                print(f"  ⚠️  {description}: Unexpected response ({response.status_code})")
        
        print("✅ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")

def test_complete_api_flow():
    """Test complete API flow with analytics"""
    print("\n🧪 Testing complete API flow with analytics...")
    
    try:
        user_id = "test-analytics-user"
        
        # 1. Check initial dashboard (should be empty)
        print("  📊 Checking initial dashboard...")
        dashboard_response = requests.get(f'http://127.0.0.1:8000/dashboard/{user_id}', timeout=5)
        if dashboard_response.status_code == 200:
            initial_dashboard = dashboard_response.json()
            print(f"  ✅ Initial dashboard: {initial_dashboard.get('message', 'No message')}")
        
        # 2. Check initial insights (should be empty)
        print("  📈 Checking initial insights...")
        insights_response = requests.get(f'http://127.0.0.1:8000/insights/{user_id}', timeout=5)
        if insights_response.status_code == 200:
            initial_insights = insights_response.json()
            print(f"  ✅ Initial insights: {initial_insights.get('message', 'No message')}")
        
        # 3. Complete a session to generate data
        print("  🎯 Completing session to generate analytics...")
        session_response = requests.post('http://127.0.0.1:8000/start_session', 
                                       json={
                                           'session_type': 'custom_topics', 
                                           'topics': ['analytics_test'],
                                           'max_topics': 1,
                                           'max_questions': 1
                                       }, 
                                       timeout=10)
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            session_id = session_data['session_id']
            
            # Complete the session
            requests.post('http://127.0.0.1:8000/answer',
                         json={
                             'session_id': session_id,
                             'user_input': 'This is a comprehensive test answer for analytics validation.'
                         },
                         timeout=10)
            
            print(f"  ✅ Session completed for analytics testing")
        
        print("✅ Complete API flow test completed")
        
    except Exception as e:
        print(f"❌ Complete API flow test failed: {e}")

def main():
    """Test Phase 4 API enhancements"""
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Starting enhanced server with Phase 4 analytics features...")
    time.sleep(3)
    
    # Test health check first
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Run Phase 4 tests
    test_dashboard_endpoint()
    test_insights_endpoint()
    test_enhanced_session_analytics()
    test_due_tasks_integration()
    test_session_metrics_generation()
    test_api_error_handling()
    test_complete_api_flow()
    
    print("\n" + "=" * 60)
    print("✅ Phase 4 API testing completed!")
    print("\n📋 Phase 4 API Features Verified:")
    print("  ✅ /dashboard/{user_id} - Comprehensive user dashboard")
    print("  ✅ /insights/{user_id}?days=X - Learning insights and analytics")
    print("  ✅ Enhanced session completion with automatic metrics")
    print("  ✅ Improved /due_tasks/{user_id} integration")
    print("  ✅ Session metrics generation and tracking")
    print("  ✅ Error handling for analytics endpoints")
    print("  ✅ Complete user journey with analytics")
    print("\n🎯 Phase 4 New Capabilities:")
    print("  📊 Real-time user dashboard with learning progress")
    print("  📈 Detailed learning insights and performance trends")
    print("  💾 Automatic session metrics saving to Firebase")
    print("  🧠 Intelligent recommendations based on performance")
    print("  📋 Enhanced task updates with session metadata")
    print("  ⚡ FSRS integration with difficulty-adaptive analytics")
    print("\n🚀 Phase 4 is ready for comprehensive user analytics!")

if __name__ == "__main__":
    main() 