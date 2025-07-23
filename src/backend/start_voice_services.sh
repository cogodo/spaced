#!/bin/bash

# Start Voice Services Script for Spaced Learning App
# This script starts all necessary services for voice functionality

echo "🚀 Starting Voice Services for Spaced Learning App"
echo "================================================"

# Check if environment variables are set
check_env_vars() {
    local missing_vars=()
    
    [ -z "$LIVEKIT_API_KEY" ] && missing_vars+=("LIVEKIT_API_KEY")
    [ -z "$LIVEKIT_API_SECRET" ] && missing_vars+=("LIVEKIT_API_SECRET")
    [ -z "$LIVEKIT_SERVER_URL" ] && missing_vars+=("LIVEKIT_SERVER_URL")
    [ -z "$OPENAI_API_KEY" ] && missing_vars+=("OPENAI_API_KEY")
    [ -z "$CARTESIA_API_KEY" ] && missing_vars+=("CARTESIA_API_KEY")
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        echo ""
        echo "Please set these in src/backend/.env file"
        exit 1
    fi
    
    echo "✅ All required environment variables are set"
}

# Start backend server
start_backend() {
    echo ""
    echo "1. Starting Backend Server..."
    cd src/backend
    
    # Check if backend is already running
    if lsof -i :8000 > /dev/null 2>&1; then
        echo "   ⚠️  Backend already running on port 8000"
    else
        echo "   Starting backend on port 8000..."
        python -m uvicorn app.main:app --reload --port 8000 &
        BACKEND_PID=$!
        sleep 3
        
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "   ✅ Backend started successfully (PID: $BACKEND_PID)"
        else
            echo "   ❌ Failed to start backend"
            exit 1
        fi
    fi
}

# Start voice agent worker
start_voice_agent() {
    echo ""
    echo "2. Starting Voice Agent Worker..."
    cd src/backend
    
    # Check if voice agent is already running
    if pgrep -f "voice_agent_worker.py" > /dev/null; then
        echo "   ⚠️  Voice agent already running"
    else
        echo "   Starting voice agent worker..."
        python voice_agent_worker.py &
        AGENT_PID=$!
        sleep 3
        
        if kill -0 $AGENT_PID 2>/dev/null; then
            echo "   ✅ Voice agent started successfully (PID: $AGENT_PID)"
        else
            echo "   ❌ Failed to start voice agent"
            exit 1
        fi
    fi
}

# Start Flutter app
start_flutter() {
    echo ""
    echo "3. Starting Flutter App..."
    cd flutter_app
    
    echo "   Running Flutter app in Chrome..."
    flutter run -d chrome &
    FLUTTER_PID=$!
    
    echo "   ✅ Flutter app starting (PID: $FLUTTER_PID)"
}

# Main execution
cd "$(dirname "$0")"  # Ensure we're in the project root

echo ""
check_env_vars

# Load environment variables
cd src/backend
source .env
cd ../..

start_backend
start_voice_agent
start_flutter

echo ""
echo "================================================"
echo "✅ All services started successfully!"
echo ""
echo "Voice Integration Test Steps:"
echo "1. Open the Flutter app in Chrome"
echo "2. Start a chat session"
echo "3. Click the microphone button (bottom right)"
echo "4. Allow microphone permissions when prompted"
echo "5. Speak to test voice input"
echo ""
echo "Monitor logs:"
echo "- Backend: src/backend/logs/"
echo "- Voice Agent: src/backend/voice_agent.log"
echo "- Flutter: Check browser console (F12)"
echo ""
echo "To stop all services: Press Ctrl+C"
echo "================================================"

# Wait for Ctrl+C
wait 