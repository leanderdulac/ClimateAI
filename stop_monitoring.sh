#!/bin/bash

# ClimateWise Monitoring Stack Stop Script

echo "🛑 Stopping ClimateWise Monitoring Stack..."

# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

echo "✅ Monitoring stack stopped successfully!"
