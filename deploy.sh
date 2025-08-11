#!/bin/bash

# FlavorForge API Deployment Script for Digital Ocean
# Usage: ./deploy.sh <droplet-ip> <username>

set -e

DROPLET_IP=$1
USERNAME=${2:-root}
APP_NAME="flavorforge-api"
REMOTE_DIR="/var/www/$APP_NAME"

if [ -z "$DROPLET_IP" ]; then
    echo "Usage: ./deploy.sh <droplet-ip> [username]"
    echo "Example: ./deploy.sh 165.227.123.45 root"
    exit 1
fi

echo "🚀 Deploying FlavorForge API to $DROPLET_IP"

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf flavorforge-api.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='deploy.sh' \
    .

# Copy files to server
echo "📤 Copying files to server..."
scp flavorforge-api.tar.gz $USERNAME@$DROPLET_IP:/tmp/

# Connect and setup server
echo "🔧 Setting up server..."
ssh $USERNAME@$DROPLET_IP << 'EOF'
    # Update system
    apt update && apt upgrade -y
    
    # Install Python 3.11 and dependencies
    apt install -y python3.11 python3.11-venv python3-pip nginx supervisor git
    
    # Create application directory
    mkdir -p /var/www/flavorforge-api
    cd /var/www/flavorforge-api
    
    # Extract application files
    tar -xzf /tmp/flavorforge-api.tar.gz -C /var/www/flavorforge-api
    
    # Create virtual environment
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn
    
    # Create systemd service
    cat > /etc/systemd/system/flavorforge-api.service << 'SERVICE'
[Unit]
Description=FlavorForge API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/flavorforge-api
Environment=PATH=/var/www/flavorforge-api/venv/bin
ExecStart=/var/www/flavorforge-api/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

    # Set permissions
    chown -R www-data:www-data /var/www/flavorforge-api
    
    # Configure Nginx
    cat > /etc/nginx/sites-available/flavorforge-api << 'NGINX'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 4G;
    
    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://127.0.0.1:8000;
    }
    
    location /static {
        # Handle static files
        alias /var/www/flavorforge-api/static;
    }
}
NGINX

    # Enable site
    ln -sf /etc/nginx/sites-available/flavorforge-api /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    # Start services
    systemctl daemon-reload
    systemctl enable flavorforge-api
    systemctl start flavorforge-api
    systemctl enable nginx
    systemctl restart nginx
    
    # Setup firewall
    ufw allow 22
    ufw allow 80
    ufw allow 443
    ufw --force enable
    
    echo "✅ Deployment completed!"
    echo "🌐 Your API should be available at: http://$(curl -s ifconfig.me)"
    echo "📊 Check status with: systemctl status flavorforge-api"
    
EOF

# Cleanup
rm flavorforge-api.tar.gz

echo "🎉 Deployment completed successfully!"
echo "🔗 Your API should be accessible at: http://$DROPLET_IP"
echo "📚 API Documentation: http://$DROPLET_IP/docs"
