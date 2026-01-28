#!/bin/bash
set -e

# Start work on a feature
# Usage: ./scripts/agent-start.sh <feature-name>

FEATURE=$1

if [ -z "$FEATURE" ]; then
    echo "Usage: ./scripts/agent-start.sh <feature-name>"
    echo "Example: ./scripts/agent-start.sh voice-agent"
    exit 1
fi

BRANCH="feature/$FEATURE"

echo "=== Starting work on: $FEATURE ==="

# Ensure we're on main and up to date
git checkout main
git pull origin main

# Create and switch to feature branch
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Branch $BRANCH exists, switching to it"
    git checkout "$BRANCH"
    git pull origin "$BRANCH" 2>/dev/null || true
else
    echo "Creating new branch: $BRANCH"
    git checkout -b "$BRANCH"
fi

echo ""
echo "✓ Ready to work on $BRANCH"
echo "Next: Read the spec and start implementing"
