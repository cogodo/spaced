#!/bin/bash
set -e
set -x

# --- Configuration ---
DOMAIN="getspaced.app"
APP_USER="appuser"
APP_HOME="/home/$APP_USER"
SRC_DIR="$APP_HOME/src"
SERVICE_ACCOUNT_JSON_PATH="$APP_HOME/firebase_service_account.json"
GITHUB_REPO="https://github.com/cogodo/spaced.git"
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

# 4. As appuser: clone or update the repo
sudo -iu "$APP_USER" bash << EOF
set -e
SRC_DIR="/home/appuser/src"
GITHUB_REPO="https://github.com/cogodo/spaced.git"
GIT_BRANCH="main"

if [ -d "\$SRC_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd "\$SRC_DIR"
    git fetch origin "\$GIT_BRANCH"
    git reset --hard "origin/\$GIT_BRANCH"
else
    echo "Cloning new repository..."
    git clone --branch "\$GIT_BRANCH" "\$GITHUB_REPO" "\$SRC_DIR"
fi
EOF

# 5. Set up Python environment with uv
echo "Setting up Python environment..."
sudo -iu "$APP_USER" bash << EOF
set -e
APP_HOME="/home/appuser"
SRC_DIR="\$APP_HOME/src"
UV_CACHE_DIR="\$APP_HOME/.cache/uv"

# Find the correct backend directory with pyproject.toml
if [ -f "\$SRC_DIR/src/backend/pyproject.toml" ]; then
    BACKEND_DIR="\$SRC_DIR/src/backend"
elif [ -f "\$SRC_DIR/backend/pyproject.toml" ]; then
    BACKEND_DIR="\$SRC_DIR/backend"
else
    echo "Error: Could not find pyproject.toml in expected locations"
    echo "Checking \$SRC_DIR/src/backend/ and \$SRC_DIR/backend/"
    find "\$SRC_DIR" -name "pyproject.toml" -type f
    exit 1
fi

echo "Using backend directory: \$BACKEND_DIR"
VENV_DIR="\$BACKEND_DIR/.venv"

cd "\$BACKEND_DIR"
mkdir -p "\$UV_CACHE_DIR"
uv venv --cache-dir "\$UV_CACHE_DIR"
source "\$VENV_DIR/bin/activate"
uv pip install --upgrade pip
uv pip install -e .
EOF

# 6. Create .env file
echo "Creating .env file..."

# Find the correct backend directory for .env file
if [ -f "$SRC_DIR/src/backend/pyproject.toml" ]; then
    BACKEND_DIR="$SRC_DIR/src/backend"
elif [ -f "$SRC_DIR/backend/pyproject.toml" ]; then
    BACKEND_DIR="$SRC_DIR/backend"
else
    echo "Error: Could not find pyproject.toml for .env file creation"
    exit 1
fi

ENV_FILE="$BACKEND_DIR/.env"

sudo -u "$APP_USER" tee "$ENV_FILE" > /dev/null << EOF
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID
FIREBASE_SERVICE_ACCOUNT_JSON=\$(cat $SERVICE_ACCOUNT_JSON_PATH)
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=$OPENAI_API_KEY
CORS_ORIGINS="https://getspaced.app,https://api.getspaced.app"
EOF
sudo chmod 600 "$ENV_FILE"
sudo chown "$APP_USER:$APP_USER" "$ENV_FILE"

# 7. Create systemd unit for backend
echo "Creating systemd service file..."

# Find the correct backend directory for systemd service
if [ -f "$SRC_DIR/src/backend/pyproject.toml" ]; then
    BACKEND_DIR="$SRC_DIR/src/backend"
elif [ -f "$SRC_DIR/backend/pyproject.toml" ]; then
    BACKEND_DIR="$SRC_DIR/backend"
else
    echo "Error: Could not find pyproject.toml for systemd service configuration"
    exit 1
fi

VENV_DIR="$BACKEND_DIR/.venv"
ENV_FILE="$BACKEND_DIR/.env"

sudo tee /etc/systemd/system/backend.service > /dev/null << EOF
[Unit]
Description=Spaced FastAPI Backend
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$ENV_FILE
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

echo "Deployment complete!"
echo "Your API should be available at https://api.$DOMAIN"
echo "To tail logs: sudo journalctl -u backend.service -f" 