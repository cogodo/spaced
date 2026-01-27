#!/bin/bash
set -e

# Simple Docker deployment script
# Run once manually to set up, then GitHub Actions calls it on push

APP_DIR="/home/ec2-user/spaced"
BACKEND_DIR="$APP_DIR/src/backend"

echo "=== Deploying Spaced Backend ==="

# Pull latest code
cd "$APP_DIR"
git fetch origin main
git reset --hard origin/main

# Build and restart
cd "$BACKEND_DIR"
docker compose down
docker compose up -d --build

# Show status
echo ""
echo "=== Deployment Complete ==="
docker compose ps
echo ""
echo "Logs: docker compose logs -f"
