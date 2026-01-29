#!/bin/bash

# Run both backend and frontend locally
cd "$(dirname "$0")"

trap "kill 0" EXIT

# Backend
echo "Starting backend on http://localhost:8000"
cd src/backend
if [ ! -d ".venv" ]; then
    uv venv
    uv pip install -e .
fi
source .venv/bin/activate
set -a && source .env && set +a
uvicorn app.main:app --reload --port 8000 &

# Voice agent worker (runs alongside backend for LiveKit sessions)
echo "Starting voice agent worker (LiveKit dev mode)"
python voice_agent_worker.py dev &

# Frontend
echo "Starting frontend on http://localhost:8080"
cd ../../flutter_app
flutter run -d web-server --web-port 8080 &

wait
