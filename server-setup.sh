#!/bin/bash
set -e

# ONE-TIME server setup - no Docker, just Python + systemd
# Run: curl -sL https://raw.githubusercontent.com/cogodo/spaced/main/server-setup.sh | bash

DOMAIN="getspaced.app"
CERTBOT_EMAIL="cogo@umich.edu"
APP_DIR="/home/ec2-user/spaced"
BACKEND_DIR="$APP_DIR/src/backend"

echo "=== Spaced Server Setup (Simple) ==="

# 1. Install system packages
echo "[1/6] Installing system packages..."
sudo yum update -y
sudo yum install -y python3 python3-pip git nginx certbot python3-certbot-nginx

# 2. Clone repo
echo "[2/6] Cloning repository..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull origin main
else
    git clone https://github.com/cogodo/spaced.git "$APP_DIR"
fi

# 3. Setup Python virtual environment
echo "[3/6] Setting up Python environment..."
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

# 4. Create systemd service
echo "[4/6] Creating systemd service..."
sudo tee /etc/systemd/system/backend.service > /dev/null << EOF
[Unit]
Description=Spaced Backend
After=network.target

[Service]
User=ec2-user
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$BACKEND_DIR/.env
ExecStart=$BACKEND_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable backend

# 5. Setup nginx
echo "[5/6] Configuring Nginx..."
sudo tee /etc/nginx/conf.d/api.conf > /dev/null << EOF
server {
    listen 80;
    server_name api.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

sudo nginx -t && sudo systemctl enable nginx && sudo systemctl restart nginx

# 6. SSL certificate
echo "[6/6] Getting SSL certificate..."
sudo certbot --nginx --non-interactive --agree-tos -m "$CERTBOT_EMAIL" -d "api.$DOMAIN" || echo "Certbot failed - run manually: sudo certbot --nginx -d api.$DOMAIN"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "NEXT STEPS:"
echo "1. Copy your secrets from local machine:"
echo "   scp src/backend/.env lightsail:$BACKEND_DIR/"
echo "   scp src/backend/firebase_service_account.json lightsail:$BACKEND_DIR/"
echo ""
echo "2. Start the backend:"
echo "   sudo systemctl start backend"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status backend"
echo "   curl http://localhost:8000/api/v1/"
