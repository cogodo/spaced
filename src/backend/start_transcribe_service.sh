#!/bin/bash

# Start the transcribe FastAPI service
echo "Starting Transcribe FastAPI Service..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Make sure DEEPGRAM_API_KEY is set."
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements_transcribe.txt

# Start the service
echo "Starting FastAPI server on port 8000..."
uvicorn main_transcribe:app --reload --port 8000 