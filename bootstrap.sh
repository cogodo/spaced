#!/bin/bash
set -e
set -x

# --- Configuration ---
DOMAIN="getspaced.app"
APP_USER="appuser"
APP_HOME="/home/$APP_USER"
BACKEND_DIR="$APP_HOME/backend" # Simplified path
SERVICE_ACCOUNT_JSON_PATH="$APP_HOME/firebase_service_account.json"
GITHUB_REPO="cogodo/spaced" # Format for git archive
GIT_BRANCH="main"
CERTBOT_EMAIL="cogo@umich.edu"

# --- Deployment ---

# 1. System update & install core packages
echo "Updating system and installing packages..."
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx certbot python3-certbot-nginx

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
GIT_BRANCH="main"

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
ENV_FILE="$APP_HOME/.backend.env" # Place env file outside the code directory

sudo -u root tee "$ENV_FILE" > /dev/null << EOF
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=$OPENAI_API_KEY
CORS_ORIGINS='["https://getspaced.app","https://api.getspaced.app"]'
EOF
sudo chmod 600 "$ENV_FILE"
sudo chown "$APP_USER:$APP_USER" "$ENV_FILE"

# 7. Create systemd unit for backend
echo "Creating systemd service file..."
VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$APP_HOME/.backend.env"

sudo tee /etc/systemd/system/backend.service > /dev/null << EOF
[Unit]
Description=Spaced FastAPI Backend
After=network.target

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

[Install]
WantedBy=multi-user.target
EOF

# 8. Enable & start the backend service
echo "Starting backend service..."
sudo systemctl daemon-reload
sudo systemctl enable backend.service
sudo systemctl restart backend.service

# 9. Configure Nginx for api.$DOMAIN
echo "Configuring Nginx..."
sudo tee /etc/nginx/conf.d/api.conf > /dev/null << EOF
server {
    listen 80;
    server_name api.$DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.$DOMAIN;

    # SSL Configuration (Certbot will handle this)
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

# 10. Obtain a certificate for api.$DOMAIN
echo "Obtaining SSL certificate..."
sudo certbot --nginx --non-interactive --agree-tos -m "$CERTBOT_EMAIL" -d "api.$DOMAIN"

# 11. Test Nginx configuration and reload
sudo nginx -t && sudo systemctl reload nginx

# 12. Copy backup environment file into the backend directory
echo "Copying backup environment file into backend directory..."
if [ -f "$APP_HOME/env.backup" ]; then
    sudo -u "$APP_USER" cp "$APP_HOME/env.backup" "$BACKEND_DIR/.env"
else
    echo "Warning: $APP_HOME/env.backup not found. Skipping copy of .env file."
fi

echo "Deployment complete!"
echo "Your API should be available at https://api.$DOMAIN"
echo "To tail logs: sudo journalctl -u backend.service -f" 