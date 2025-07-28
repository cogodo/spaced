set -e
set -x

# --- Configuration ---
DOMAIN="staging.getspaced.app"
APP_USER="appuser"
APP_HOME="/home/$APP_USER"
BACKEND_DIR="$APP_HOME/backend" # Simplified path
SERVICE_ACCOUNT_JSON_PATH="$APP_HOME/firebase_service_account.json"
GITHUB_REPO="cogodo/spaced" # Format for git archive
GIT_BRANCH="staging"
CERTBOT_EMAIL="cogo@umich.edu"

# --- Voice-to-Voice Configuration ---
# These should be set as environment variables or passed as parameters
LIVEKIT_API_KEY="${LIVEKIT_API_KEY:-}"
LIVEKIT_API_SECRET="${LIVEKIT_API_SECRET:-}"
LIVEKIT_SERVER_URL="${LIVEKIT_SERVER_URL:-}"
CARTESIA_API_KEY="${CARTESIA_API_KEY:-}"
DEEPGRAM_API_KEY="${DEEPGRAM_API_KEY:-}"

# --- Environment Detection ---
# Determine if this is staging or production based on domain
if [[ "$DOMAIN" == *"staging"* ]]; then
    ENVIRONMENT="staging"
    BACKEND_URL="https://api.staging.getspaced.app"
    echo "Detected staging environment"
else
    ENVIRONMENT="production"
    BACKEND_URL="https://api.getspaced.app"
    echo "Detected production environment"
fi

# --- Deployment ---

# 1. System update & install core packages
echo "Updating system and installing packages..."
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx certbot python3-certbot-nginx

# 1. Update your system
sudo dnf update -y

# 2. Install Redis 6
sudo dnf install -y redis6

# 3. Enable & start the Redis service
sudo systemctl enable --now redis6

# 4. Verify it's running
sudo systemctl status redis6

# 5. Test with the CLI
redis6-cli ping
# You should see: PONG

# 2. Install uv globally
echo "Installing uv..."
sudo pip3 install uv
uv python pin 3.13

# 3. Create a non-root app user
if ! id "$APP_USER" &>/dev/null; then
    echo "Creating user $APP_USER..."
    sudo useradd -m -s /bin/bash "$APP_USER"
    sudo usermod -aG wheel "$APP_USER"
fi
sudo chown -R "$APP_USER:$APP_USER" "$APP_HOME"

# 4. As appuser: download and extract ONLY the backend code
sudo -iu "$APP_USER" bash << EOF
set -e
APP_HOME="/home/appuser"
BACKEND_DIR="\$APP_HOME/backend"
GITHUB_REPO="cogodo/spaced"
GIT_BRANCH="staging"

# Remove old directories to ensure a clean deployment
rm -rf "\$BACKEND_DIR"
rm -rf "\$APP_HOME/src" # Clean up old structure

echo "Downloading and extracting backend from repository..."
cd "\$APP_HOME"
# Use git archive to download only the src/backend directory
curl -L "https://github.com/\$GITHUB_REPO/archive/\$GIT_BRANCH.tar.gz" | \
    tar -xz --strip-components=2 "spaced-\$GIT_BRANCH/src/backend"
# The 'mv' command is no longer needed as tar creates the 'backend' directory.
EOF

# 5. Set up Python environment with uv
echo "Setting up Python environment..."
sudo -iu "$APP_USER" bash << EOF
set -e
APP_HOME="/home/appuser"
BACKEND_DIR="\$APP_HOME/backend"
VENV_DIR="\$BACKEND_DIR/.venv"
UV_CACHE_DIR="\$APP_HOME/.cache/uv"

echo "Using backend directory: \$BACKEND_DIR"

cd "\$BACKEND_DIR"
mkdir -p "\$UV_CACHE_DIR"
uv venv --cache-dir "\$UV_CACHE_DIR"
source "\$VENV_DIR/bin/activate"
uv pip install --upgrade pip
uv pip install -e .
EOF

# 6. Create .env file for systemd service (separate from code)
echo "Creating .env file..."
ENV_FILE="$APP_HOME/.env" # Place env file outside the code directory

echo "Copying backup environment file into backend directory..."
if [ -f "$APP_HOME/env.backup" ]; then
    sudo -u "$APP_USER" cp "$APP_HOME/env.backup" "$ENV_FILE"
else
    echo "Warning: $APP_HOME/env.backup not found. Skipping copy of .env file."
fi

# Add voice-to-voice configuration to .env file
echo "Adding voice-to-voice configuration to .env file..."
sudo -u "$APP_USER" tee -a "$ENV_FILE" > /dev/null << EOF

# Environment Configuration
ENVIRONMENT=$ENVIRONMENT
BACKEND_URL=$BACKEND_URL

# Voice-to-Voice Configuration
LIVEKIT_API_KEY=$LIVEKIT_API_KEY
LIVEKIT_API_SECRET=$LIVEKIT_API_SECRET
LIVEKIT_SERVER_URL=$LIVEKIT_SERVER_URL
CARTESIA_API_KEY=$CARTESIA_API_KEY
DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY
EOF

sudo chmod 600 "$ENV_FILE"
sudo chown "$APP_USER:$APP_USER" "$ENV_FILE"

# 7. Create systemd unit for backend
echo "Creating systemd service file..."
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$APP_HOME/.env"

sudo tee /etc/systemd/system/backend.service > /dev/null << EOF
[Unit]
Description=Spaced FastAPI Backend
After=network.target redis6.service
Before=voice-agent.service

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$BACKEND_DIR
# Load env vars from the file and the Firebase secret directly
EnvironmentFile=$ENV_FILE
Environment="FIREBASE_SERVICE_ACCOUNT_JSON=\$(cat $SERVICE_ACCOUNT_JSON_PATH)"
ExecStart=$VENV_DIR/bin/start-backend
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 8. Create systemd unit for voice agent worker
echo "Creating voice agent systemd service file..."
sudo tee /etc/systemd/system/voice-agent.service > /dev/null << EOF
[Unit]
Description=Spaced Voice Agent Worker
After=network.target backend.service
Requires=backend.service

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
Environment="FIREBASE_SERVICE_ACCOUNT_JSON=\$(cat $SERVICE_ACCOUNT_JSON_PATH)"
ExecStart=$VENV_DIR/bin/python voice_agent_worker.py start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 9. Create logs directory
echo "Creating logs directory..."
sudo mkdir -p /var/log/spaced
sudo chown "$APP_USER:$APP_USER" /var/log/spaced

# 10. Enable & start the services
echo "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable backend.service
sudo systemctl enable voice-agent.service
sudo systemctl restart backend.service
sudo systemctl restart voice-agent.service

# 11. Create health check script
echo "Creating health check script..."
sudo tee /usr/local/bin/spaced-health-check > /dev/null << 'EOF'
#!/bin/bash
# Health check for all Spaced services

check_service() {
    local service_name=$1
    if systemctl is-active --quiet $service_name; then
        echo "✅ $service_name: Running"
        return 0
    else
        echo "❌ $service_name: Not running"
        return 1
    fi
}

echo "Spaced Services Health Check"
echo "============================"

check_service backend.service
check_service voice-agent.service
check_service redis6

# Check API endpoints
if curl -s http://localhost:8000/api/v1/ > /dev/null; then
    echo "✅ Backend API: Responding"
else
    echo "❌ Backend API: Not responding"
fi

if curl -s http://localhost:8000/api/v1/voice/health > /dev/null; then
    echo "✅ Voice API: Responding"
else
    echo "❌ Voice API: Not responding"
fi

# Check voice environment variables
echo ""
echo "Voice Configuration Check:"
echo "=========================="

if [ -n "$LIVEKIT_API_KEY" ]; then
    echo "✅ LIVEKIT_API_KEY: Set"
else
    echo "❌ LIVEKIT_API_KEY: Not set"
fi

if [ -n "$LIVEKIT_API_SECRET" ]; then
    echo "✅ LIVEKIT_API_SECRET: Set"
else
    echo "❌ LIVEKIT_API_SECRET: Not set"
fi

if [ -n "$LIVEKIT_SERVER_URL" ]; then
    echo "✅ LIVEKIT_SERVER_URL: Set"
else
    echo "❌ LIVEKIT_SERVER_URL: Not set"
fi

if [ -n "$CARTESIA_API_KEY" ]; then
    echo "✅ CARTESIA_API_KEY: Set"
else
    echo "❌ CARTESIA_API_KEY: Not set"
fi

if [ -n "$DEEPGRAM_API_KEY" ]; then
    echo "✅ DEEPGRAM_API_KEY: Set (optional)"
else
    echo "⚠️  DEEPGRAM_API_KEY: Not set (will use OpenAI Whisper)"
fi

if [ -n "$BACKEND_URL" ]; then
    echo "✅ BACKEND_URL: Set ($BACKEND_URL)"
else
    echo "⚠️  BACKEND_URL: Not set (will auto-detect)"
fi

if [ -n "$ENVIRONMENT" ]; then
    echo "✅ ENVIRONMENT: Set ($ENVIRONMENT)"
else
    echo "⚠️  ENVIRONMENT: Not set (will auto-detect)"
fi
EOF

sudo chmod +x /usr/local/bin/spaced-health-check

# 12. Configure Nginx for api.$DOMAIN
echo "Configuring Nginx for initial Certbot validation..."
sudo tee /etc/nginx/conf.d/api.conf > /dev/null << EOF
# This is a temporary configuration for Certbot.
# It will be replaced after the certificate is obtained.
server {
    listen 80;
    server_name api.$DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 404; # Block all other traffic until SSL is ready
    }
}
EOF

# Ensure the validation directory exists and has correct permissions
sudo mkdir -p /var/www/html
sudo chown -R nginx:nginx /var/www/html

# Test and reload Nginx with the temporary config
sudo nginx -t && sudo systemctl restart nginx

# 13. Obtain a certificate for api.$DOMAIN
echo "Obtaining SSL certificate..."
sudo certbot --nginx --non-interactive --agree-tos -m "$CERTBOT_EMAIL" -d "api.$DOMAIN"

# 14. Re-configure Nginx with the final SSL configuration
echo "Configuring Nginx with final SSL settings..."
sudo tee /etc/nginx/conf.d/api.conf > /dev/null << EOF
server {
    listen 80;
    server_name api.$DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.$DOMAIN;

    # SSL Configuration (Certbot has placed the files)
    ssl_certificate /etc/letsencrypt/live/api.$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        proxy_redirect off;
    }
}
EOF

# 15. Test Nginx configuration and reload
sudo nginx -t && sudo systemctl restart nginx

# 16. Run health check
echo ""
echo "Running health check..."
/usr/local/bin/spaced-health-check

echo ""
echo "Deployment complete!"
echo "Your API should be available at https://api.$DOMAIN"
echo ""
echo "Voice-to-Voice Features:"
echo "- Voice agent worker is running as a systemd service"
echo "- Voice API health check available at /api/v1/voice/health"
echo "- Monitor voice agent logs: sudo journalctl -u voice-agent.service -f"
echo "- Run health check: /usr/local/bin/spaced-health-check"
echo ""
echo "To tail logs:"
echo "- Backend: sudo journalctl -u backend.service -f"
echo "- Voice Agent: sudo journalctl -u voice-agent.service -f"
echo ""
echo "To restart services:"
echo "- Backend: sudo systemctl restart backend.service"
echo "- Voice Agent: sudo systemctl restart voice-agent.service"