#!/bin/bash

# Local dev server
cd "$(dirname "$0")"

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "Creating venv..."
    uv venv
    uv pip install -e .
fi

source .venv/bin/activate

# Load .env
set -a && source .env && set +a

echo "Starting backend at http://localhost:8000"
uvicorn app.main:app --reload --port 8000
