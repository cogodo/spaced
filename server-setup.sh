#!/bin/bash
set -e

# ONE-TIME server setup script
# Run this manually once on a fresh server

DOMAIN="getspaced.app"
CERTBOT_EMAIL="cogo@umich.edu"
APP_DIR="/home/ec2-user/spaced"

echo "=== One-time Server Setup ==="

# 1. Install Docker
echo "Installing Docker..."
sudo yum update -y
sudo yum install -y docker git
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. Install nginx + certbot
echo "Installing Nginx..."
sudo yum install -y nginx certbot python3-certbot-nginx
sudo systemctl enable nginx

# 3. Clone repo
echo "Cloning repository..."
git clone https://github.com/cogodo/spaced.git "$APP_DIR" || (cd "$APP_DIR" && git pull)

# 4. Copy your secrets (do this manually)
echo ""
echo "=== MANUAL STEPS REQUIRED ==="
echo "1. Copy your .env file to: $APP_DIR/src/backend/.env"
echo "2. Copy firebase_service_account.json to: $APP_DIR/src/backend/"
echo ""
echo "Then run: $APP_DIR/deploy.sh"
echo ""

# 5. Setup nginx
echo "Setting up Nginx..."
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
    }
}
EOF

sudo nginx -t && sudo systemctl restart nginx

# 6. Get SSL cert
echo "Getting SSL certificate..."
sudo certbot --nginx --non-interactive --agree-tos -m "$CERTBOT_EMAIL" -d "api.$DOMAIN" || echo "Certbot failed - you may need to run it manually"

# 7. Make deploy script executable
chmod +x "$APP_DIR/deploy.sh"

echo ""
echo "=== Setup Complete ==="
echo "After copying .env and firebase credentials, run: $APP_DIR/deploy.sh"
