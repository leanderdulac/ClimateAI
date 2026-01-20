#!/bin/bash

# ClimateAI Monitoring Stack Startup Script

set -e

echo "🚀 Starting ClimateAI Monitoring Stack..."

# Create necessary directories
mkdir -p monitoring/prometheus/data
mkdir -p monitoring/grafana/data
mkdir -p monitoring/elasticsearch/data
mkdir -p monitoring/logstash/data

# Set proper permissions
chmod 777 monitoring/elasticsearch/data
chmod 777 monitoring/logstash/data

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check Prometheus
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not healthy"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not healthy"
fi

# Check Elasticsearch
if curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; then
    echo "✅ Elasticsearch is healthy"
else
    echo "❌ Elasticsearch is not healthy"
fi

echo ""
echo "🎉 Monitoring stack started successfully!"
echo ""
echo "Access URLs:"
echo "📊 Grafana: http://localhost:3000 (admin/admin)"
echo "🔥 Prometheus: http://localhost:9090"
echo "📈 Kibana: http://localhost:5601"
echo "🗄️  Elasticsearch: http://localhost:9200"
echo ""
echo "To stop the monitoring stack, run: docker-compose -f docker-compose.monitoring.yml down"
