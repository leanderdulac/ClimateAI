#!/bin/bash
echo "Checking server health..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$response" -eq 200 ]; then
  echo "Server is UP (Root endpoint returned 200 OK)"
  exit 0
else
  echo "Server is DOWN or failing (Root endpoint returned $response)"
  exit 1
fi
