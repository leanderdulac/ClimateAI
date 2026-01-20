#!/bin/bash

# ClimateAI Monitoring Stack Stop Script

echo "🛑 Stopping ClimateAI Monitoring Stack..."

# Stop monitoring stack
docker-compose -f docker-compose.monitoring.yml down

echo "✅ Monitoring stack stopped successfully!"
