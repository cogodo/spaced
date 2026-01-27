#!/bin/bash
set -e

# Simple deploy script - git pull + restart
APP_DIR="/home/ec2-user/spaced"
BACKEND_DIR="$APP_DIR/src/backend"

echo "=== Deploying ==="

cd "$APP_DIR"
git fetch origin main
git reset --hard origin/main

cd "$BACKEND_DIR"
source .venv/bin/activate
pip install -e . --quiet

sudo systemctl restart backend
sleep 2

echo "=== Status ==="
sudo systemctl status backend --no-pager | head -20
