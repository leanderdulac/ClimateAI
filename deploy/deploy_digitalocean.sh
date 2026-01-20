#!/bin/bash

# ClimateAI - Deploy Script for DigitalOcean
# This script automates the deployment of ClimateAI to DigitalOcean Droplet

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="climateai"
DOMAIN="${DOMAIN:-your-domain.com}"
EMAIL="${EMAIL:-admin@your-domain.com}"
DB_PASSWORD="${DB_PASSWORD:-CHANGE_THIS_STRONG_PASSWORD}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

print_status "🚀 Starting ClimateAI DigitalOcean Deployment..."
print_status "Domain: $DOMAIN"
print_status "Email: $EMAIL"

# Update system
print_step "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_step "2. Installing required packages..."
sudo apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    git \
    nginx \
    certbot \
    python3-certbot-nginx

# Install Docker
print_step "3. Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
print_warning "You may need to log out and back in for Docker group changes to take effect."

# Configure firewall
print_step "4. Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force reload

# Create application directory
print_step "5. Setting up application directory..."
sudo mkdir -p /opt/$APP_NAME
sudo chown -R $USER:$USER /opt/$APP_NAME

# Clone repository
print_step "6. Cloning ClimateAI repository..."
cd /opt/$APP_NAME
if [ ! -d ".git" ]; then
    git clone https://github.com/leanderdulac/ClimateAI.git .
else
    print_warning "Repository already exists, pulling latest changes..."
    git pull origin main
fi

# Create environment file
print_step "7. Creating environment configuration..."
cat > .env << EOF
# Database
DB_PASSWORD=$DB_PASSWORD
POSTGRES_PASSWORD=$DB_PASSWORD

# Application
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
DOMAIN=$DOMAIN

# External APIs (configure as needed)
OPENMETEO_API_KEY=${OPENMETEO_API_KEY:-}
EMBRAPA_API_KEY=${EMBRAPA_API_KEY:-}
EOF

print_warning "Please update the .env file with your actual API keys and secrets."

# Create Docker environment file for production
cat > server/.env << EOF
DATABASE_URL=postgresql+asyncpg://climateai_user:$DB_PASSWORD@db:5432/climateai
REDIS_URL=redis://redis:6379
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
DOMAIN=$DOMAIN
OPENMETEO_API_KEY=${OPENMETEO_API_KEY:-}
EMBRAPA_API_KEY=${EMBRAPA_API_KEY:-}
EOF

# Create data directories
print_step "8. Creating data directories..."
mkdir -p data
mkdir -p monitoring/prometheus/data
mkdir -p monitoring/grafana/data

# Set proper permissions
sudo chown -R 472:472 monitoring/grafana/data
sudo chown -R 65534:65534 monitoring/prometheus/data

# Start the application
print_step "9. Starting ClimateAI application..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
print_step "10. Waiting for services to start..."
sleep 30

# Check if services are running
print_step "11. Checking service status..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_status "✅ Services are running!"
else
    print_error "❌ Some services failed to start. Check logs with: docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

# Configure Nginx (if domain is provided)
if [ "$DOMAIN" != "your-domain.com" ]; then
    print_step "12. Configuring Nginx for domain $DOMAIN..."

    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx

    # Get SSL certificate
    print_step "13. Obtaining SSL certificate..."
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --non-interactive

    print_status "✅ SSL certificate obtained successfully!"
else
    print_warning "Domain not configured. Please set DOMAIN environment variable and run SSL setup manually."
fi

# Setup monitoring
print_step "14. Setting up monitoring..."
cd monitoring
docker-compose up -d

# Setup backup
print_step "15. Setting up automated backup..."
sudo mkdir -p /opt/backup
sudo tee /opt/backup/backup.sh > /dev/null <<EOF
#!/bin/bash
# ClimateAI Database Backup Script

BACKUP_DIR="/opt/backup"
DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="\$BACKUP_DIR/climateai_backup_\$DATE.sql"

# Create backup
docker exec climateai-db-1 pg_dump -U climateai_user -h localhost climateai > \$BACKUP_FILE

# Compress backup
gzip \$BACKUP_FILE

# Keep only last 7 days
find \$BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_FILE.gz"
EOF

sudo chmod +x /opt/backup/backup.sh

# Add backup to crontab (daily at 2 AM)
(crontab -l ; echo "0 2 * * * /opt/backup/backup.sh") | crontab -

print_status "✅ Automated daily backup configured!"

# Final status
print_status ""
print_status "🎉 ClimateAI deployment completed successfully!"
print_status ""
print_status "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

print_status ""
print_status "🌐 Access URLs:"
if [ "$DOMAIN" != "your-domain.com" ]; then
    echo "  Frontend: https://$DOMAIN"
    echo "  API: https://$DOMAIN/api"
else
    echo "  Frontend: http://YOUR_DROPLET_IP"
    echo "  API: http://YOUR_DROPLET_IP:8000"
fi

print_status ""
print_status "📈 Monitoring:"
echo "  Grafana: http://YOUR_DROPLET_IP:3001 (admin/admin)"
echo "  Prometheus: http://YOUR_DROPLET_IP:9090"

print_status ""
print_status "🔧 Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  Update: git pull && docker-compose -f docker-compose.prod.yml up -d --build"
echo "  Backup: /opt/backup/backup.sh"

print_status ""
print_warning "⚠️  IMPORTANT:"
print_warning "1. Update the .env files with your actual API keys"
print_warning "2. Change default passwords in production"
print_warning "3. Configure domain DNS to point to your droplet IP"
print_warning "4. Test the application thoroughly before going live"
print_warning "5. Monitor logs and resources regularly"

print_status ""
print_status "🚀 Deployment completed! Your ClimateAI is ready for production."
