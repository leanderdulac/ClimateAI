#!/bin/bash

# ClimateWise - Local Deploy Test Script
# Test deployment locally before pushing to production

set -e

echo "🧪 Testing ClimateWise deployment locally..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running"

# Clean up previous containers
echo "🧹 Cleaning up previous containers..."
docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
docker system prune -f

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_warning "Creating .env file from template..."
    cp .env.example .env
    # Update with test values
    sed -i 's/CHANGE_THIS_STRONG_PASSWORD/test_password_123/g' .env
    sed -i 's/CHANGE_THIS_TO_A_STRONG_RANDOM_KEY/test_secret_key_123/g' .env
fi

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    print_status "Backend is healthy"
else
    print_error "Backend is not responding"
fi

# Check frontend
if curl -f http://localhost:80 > /dev/null 2>&1; then
    print_status "Frontend is responding"
else
    print_error "Frontend is not responding"
fi

# Check database connection
if docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U climatewise_user -d climatewise > /dev/null 2>&1; then
    print_status "Database is ready"
else
    print_error "Database connection failed"
fi

# Check Redis
if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q PONG; then
    print_status "Redis is responding"
else
    print_error "Redis is not responding"
fi

echo ""
print_status "Local deployment test completed!"
echo ""
echo "🌐 Access URLs:"
echo "  Frontend: http://localhost"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "To stop: docker-compose -f docker-compose.prod.yml down"
echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
