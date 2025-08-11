# 🚀 FlavorForge API - Digital Ocean Deployment Guide

This guide will walk you through deploying your FlavorForge API to a Digital Ocean droplet.

## 📋 Prerequisites

1. **Digital Ocean Droplet** with:
   - Ubuntu 20.04 or 22.04 LTS
   - At least 1GB RAM (2GB recommended)
   - SSH access with IP address and password/key
   
2. **Local Machine**:
   - SSH client
   - Your project files ready

## 🛠️ Quick Deployment (Automated)

### Option 1: One-Command Deployment

```bash
# Make sure you're in your project directory
cd /Users/harshit/projects/codeathon-backend

# Run the automated deployment script
./deploy.sh YOUR_DROPLET_IP root
```

**Example:**
```bash
./deploy.sh 165.227.123.45 root
```

This script will:
- ✅ Update the server and install dependencies
- ✅ Install Python 3.11, Nginx, and Gunicorn
- ✅ Transfer your application files
- ✅ Set up virtual environment and install packages
- ✅ Configure systemd service for auto-restart
- ✅ Configure Nginx as reverse proxy
- ✅ Set up firewall rules
- ✅ Start all services

## 🔧 Manual Deployment (Step by Step)

If you prefer manual control or the automated script fails:

### Step 1: Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Update System and Install Dependencies

```bash
# Update package list and upgrade system
apt update && apt upgrade -y

# Install required packages
apt install -y python3.11 python3.11-venv python3-pip nginx supervisor git curl
```

### Step 3: Create Application Directory

```bash
# Create directory for your app
mkdir -p /var/www/flavorforge-api
cd /var/www/flavorforge-api
```

### Step 4: Transfer Your Files

From your local machine:

```bash
# Create archive (excluding unnecessary files)
tar -czf flavorforge-api.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    .

# Copy to server
scp flavorforge-api.tar.gz root@YOUR_DROPLET_IP:/var/www/flavorforge-api/

# Extract on server
ssh root@YOUR_DROPLET_IP
cd /var/www/flavorforge-api
tar -xzf flavorforge-api.tar.gz
```

### Step 5: Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### Step 6: Create Systemd Service

```bash
# Create service file
cat > /etc/systemd/system/flavorforge-api.service << 'EOF'
[Unit]
Description=FlavorForge API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/flavorforge-api
Environment=PATH=/var/www/flavorforge-api/venv/bin
ExecStart=/var/www/flavorforge-api/venv/bin/gunicorn -c gunicorn.conf.py main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

### Step 7: Configure Nginx

```bash
# Create Nginx configuration
cat > /etc/nginx/sites-available/flavorforge-api << 'EOF'
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
        alias /var/www/flavorforge-api/static;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/flavorforge-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
```

### Step 8: Set Permissions and Start Services

```bash
# Set proper permissions
chown -R www-data:www-data /var/www/flavorforge-api

# Create log directory
mkdir -p /var/log
touch /var/log/flavorforge-api-access.log
touch /var/log/flavorforge-api-error.log
chown www-data:www-data /var/log/flavorforge-api*.log

# Enable and start services
systemctl daemon-reload
systemctl enable flavorforge-api
systemctl start flavorforge-api
systemctl enable nginx
systemctl restart nginx
```

### Step 9: Configure Firewall

```bash
# Allow SSH, HTTP, and HTTPS
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
```

## 🔍 Verification and Testing

### Check Service Status

```bash
# Check if your API service is running
systemctl status flavorforge-api

# Check Nginx status
systemctl status nginx

# View logs
journalctl -u flavorforge-api -f
tail -f /var/log/flavorforge-api-error.log
```

### Test Your API

```bash
# Test locally on the server
curl http://localhost:8000/

# Test from your local machine
curl http://YOUR_DROPLET_IP/

# Test specific endpoints
curl http://YOUR_DROPLET_IP/api/dashboard/metrics
curl http://YOUR_DROPLET_IP/api/products
curl http://YOUR_DROPLET_IP/api/market-trends
curl http://YOUR_DROPLET_IP/api/competitors

# View API documentation
# Open browser: http://YOUR_DROPLET_IP/docs
```

## 🚀 Your API Endpoints

Once deployed, your API will be available at:

- **Base URL**: `http://YOUR_DROPLET_IP`
- **API Documentation**: `http://YOUR_DROPLET_IP/docs`
- **OpenAPI Schema**: `http://YOUR_DROPLET_IP/openapi.json`

### Available Endpoints:

1. **Dashboard Metrics**: `GET /api/dashboard/metrics`
2. **Products**: `GET /api/products` and `POST /api/products`
3. **Market Trends**: `GET /api/market-trends`
4. **Product Analysis**: `POST /api/analyze-product`
5. **Competitors**: `GET /api/competitors`

## 🔄 Updating Your Application

To update your application after making changes:

```bash
# From your local machine, re-run the deployment script
./deploy.sh YOUR_DROPLET_IP root

# Or manually:
# 1. Create new archive and transfer
# 2. Extract in /var/www/flavorforge-api
# 3. Restart the service
ssh root@YOUR_DROPLET_IP
systemctl restart flavorforge-api
```

## 🛡️ Security Recommendations

1. **Change default SSH port** (optional but recommended)
2. **Set up SSL/HTTPS** with Let's Encrypt:
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```
3. **Configure proper firewall rules**
4. **Set up monitoring and backups**
5. **Use environment variables for sensitive data**

## 🐛 Troubleshooting

### Common Issues:

1. **Service won't start**:
   ```bash
   # Check logs
   journalctl -u flavorforge-api -n 50
   
   # Check if port is in use
   lsof -i :8000
   ```

2. **Nginx errors**:
   ```bash
   # Test configuration
   nginx -t
   
   # Check logs
   tail -f /var/log/nginx/error.log
   ```

3. **Permission errors**:
   ```bash
   # Fix permissions
   chown -R www-data:www-data /var/www/flavorforge-api
   ```

4. **Python/dependency issues**:
   ```bash
   # Reinstall dependencies
   cd /var/www/flavorforge-api
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📞 Support

If you encounter issues:
1. Check the logs first: `journalctl -u flavorforge-api -f`
2. Verify all files are present and permissions are correct
3. Test individual components (Python app, Nginx, firewall)

Your FlavorForge API should now be live and accessible! 🎉
