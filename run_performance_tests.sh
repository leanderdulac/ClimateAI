#!/bin/bash

# ClimateAI Performance Testing Script

set -e

echo "🏃 Starting ClimateAI Performance Tests..."

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo "Installing Locust..."
    pip install locust locust-plugins
fi

# Create results directory
mkdir -p server/tests/performance/results

# Run performance tests
echo "Running performance tests..."
locust -f server/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users=10 \
       --spawn-rate=2 \
       --run-time=1m \
       --csv=server/tests/performance/results/test_results \
       --html=server/tests/performance/results/report.html \
       --headless

echo "✅ Performance tests completed!"
echo "📊 Results saved to server/tests/performance/results/"