#!/bin/bash
# Start ClimateWise Backend - Development Mode (without database)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
  VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python"
elif [ -x "$SCRIPT_DIR/venv-hathor/bin/python3" ]; then
  VENV_PYTHON="$SCRIPT_DIR/venv-hathor/bin/python3"
else
  echo "❌ Nenhum ambiente Python utilizável encontrado (.venv ou venv-hathor)"
  exit 1
fi

# Set environment variables for development (no database)
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export DATABASE_ENABLED=false
export SECRET_KEY="${SECRET_KEY:-$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)}"
export DEBUG=true
export ALLOW_ORIGINS="http://localhost:5173,http://localhost:3000"

# Kill any existing uvicorn processes
pkill -f "uvicorn.*main:app" 2>/dev/null || true
sleep 2

# Start server
echo "Starting ClimateWise backend in development mode..."
echo "Database: DISABLED (using in-memory SQLite)"
echo "API Docs: http://localhost:8000/docs"
echo ""

nohup "$VENV_PYTHON" -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir blockchain \
  --reload-dir api \
  > /tmp/server.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to start
echo "Waiting for server to start..."
for i in {1..30}; do
  if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ Server is ready!"
    echo ""
    echo "Access points:"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Hathor API: http://localhost:8000/api/v1/blockchain/hathor"
    echo "  - Oracle API: http://localhost:8000/api/v1/blockchain/hathor/oracle"
    echo ""
    exit 0
  fi
  sleep 1
done

echo "❌ Server failed to start. Check logs:"
tail -50 /tmp/server.log
exit 1
