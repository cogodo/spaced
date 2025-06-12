#!/usr/bin/env python3
"""
API test for Phase 2 endpoints
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

def test_endpoints():
    """Test the new Phase 2 endpoints"""
    print("🧪 Testing Phase 2 API endpoints...")
    
    # Test health check first
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test due_tasks endpoint (will fail without Firebase, but should return proper error)
    try:
        print("\n🧪 Testing /due_tasks endpoint...")
        response = requests.get('http://127.0.0.1:8000/due_tasks/test_user', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 500:
            print("Expected error due to no Firebase credentials")
        else:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error (expected without Firebase): {e}")

    # Test start_session with custom topics (should work)
    try:
        print("\n🧪 Testing start_session with custom topics...")
        response = requests.post('http://127.0.0.1:8000/start_session', 
                               json={
                                   'session_type': 'custom_topics', 
                                   'topics': ['python', 'react'],
                                   'max_topics': 2,
                                   'max_questions': 3
                               }, 
                               timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Session started: {data.get('session_id')}")
            print(f"Message: {data.get('message')}")
            print(f"Topics count: {data.get('topics_count')}")
            print(f"First question: {data.get('next_question')[:50]}...")
        else:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n✅ Phase 2 API testing completed!")

if __name__ == "__main__":
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("Starting server...")
    time.sleep(3)
    
    # Run tests
    test_endpoints() 