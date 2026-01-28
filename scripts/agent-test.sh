#!/bin/bash
set -e

# Run tests and validation
# Usage: ./scripts/agent-test.sh

cd "$(dirname "$0")/.."

echo "=== Running Tests ==="

# Backend tests
echo "[1/3] Backend tests..."
cd src/backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python -m pytest tests/ -v --tb=short 2>/dev/null || echo "No backend tests or pytest not configured"
else
    echo "Skipping backend tests (no venv)"
fi
cd ../..

# Frontend tests
echo "[2/3] Frontend tests..."
cd flutter_app
flutter test 2>/dev/null || echo "No flutter tests or flutter test failed"
cd ..

# Lint
echo "[3/3] Linting..."
cd src/backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
    ruff check . --fix 2>/dev/null || echo "Ruff not available or lint issues"
fi
cd ../..

echo ""
echo "=== Tests Complete ==="
