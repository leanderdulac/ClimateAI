#!/bin/bash

# Production Setup Script for ClimateAI
# This script prepares the environment for production deployment

set -e

echo "🚀 Starting ClimateAI Production Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose \
    git \
    curl \
    ufw

# Start and enable services
print_status "Starting and enabling services..."
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start nginx
sudo systemctl enable nginx

# Configure PostgreSQL
print_status "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE climateai;" 2>/dev/null || print_warning "Database climateai may already exist"
sudo -u postgres psql -c "CREATE USER climateai_user WITH PASSWORD 'CHANGE_THIS_STRONG_PASSWORD';" 2>/dev/null || print_warning "User climateai_user may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE climateai TO climateai_user;"

# Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000  # FastAPI port
sudo ufw allow 3000  # Frontend port

# Create application directory
print_status "Setting up application directory..."
sudo mkdir -p /opt/climateai
sudo chown -R $USER:$USER /opt/climateai

# Clone or copy application code (assuming it's already in place)
# cd /opt/climateai
# git clone https://github.com/leanderdulac/ClimateAI.git .

# Set up Python virtual environment
print_status "Setting up Python virtual environment..."
cd /opt/climateai/server
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations (assuming Alembic is set up)
print_status "Running database migrations..."
alembic upgrade head

# Configure environment variables
print_status "Configuring environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Production Environment Variables
HOST=0.0.0.0
PORT=8000
DEBUG=False
API_HOST=yourdomain.com
API_PORT=443
SECRET_KEY=$(openssl rand -hex 32)
ALLOW_ORIGINS=["https://yourdomain.com"]
DATABASE_URL=postgresql://climateai_user:CHANGE_THIS_STRONG_PASSWORD@localhost/climateai
REDIS_URL=redis://localhost:6379
OPENMETEO_API_URL=https://api.open-meteo.com
EMBRAPA_API_URL=https://api.cnptia.embrapa.br/agritec
EMBRAPA_API_VERSION=v1
EMBRAPA_API_KEY=your-embrapa-api-key-if-needed
LOG_LEVEL=INFO
OPENMETEO_CACHE_DIR=.cache
OPENMETEO_CACHE_TIMEOUT=3600
GEOCODING_CACHE_TIMEOUT=86400
GEOCODING_MAX_RETRIES=3
EOF
    print_warning "Generated .env file. Please update DATABASE_URL password and other sensitive values!"
else
    print_warning ".env file already exists. Please review and update as needed."
fi

# Build and start containers
print_status "Building and starting Docker containers..."
cd /opt/climateai
docker-compose -f docker-compose.prod.yml up -d --build

# Configure Nginx as reverse proxy
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/climateai > /dev/null <<EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/climateai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Set up SSL certificate (optional, requires domain)
# sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Configure monitoring (basic setup)
print_status "Setting up basic monitoring..."
# Add Prometheus and Grafana setup here if needed

print_status "Production setup completed!"
print_warning "Next steps:"
echo "1. Update passwords in .env file"
echo "2. Configure your domain in Nginx config"
echo "3. Set up SSL certificate with certbot"
echo "4. Configure monitoring alerts"
echo "5. Test the application thoroughly"

print_status "Application should be accessible at:"
echo "- Frontend: http://yourdomain.com"
echo "- API: http://yourdomain.com/api"
echo "- API Docs: http://yourdomain.com/api/docs"
