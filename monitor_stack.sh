#!/bin/bash
# Script de monitoramento contínuo do stack ClimateAI
# Reinicia frontend automaticamente se porta 3000 estiver ocupada e serviço não responder
# Reinicia backend se health check falhar
# Loga eventos e status

LOG_FILE="monitor_stack.log"
FRONTEND_PORT=3000
BACKEND_PORT=8000
LANDING_PORT=8080
BACKEND_HEALTH_URL="http://localhost:8000/health"
FRONTEND_URL="http://localhost:3000/"
LANDING_URL="http://localhost:8080/landing-page.html"

check_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t >/dev/null
}

restart_frontend() {
    echo "[$(date)] Reiniciando frontend..." | tee -a "$LOG_FILE"
    ./stop_platform.sh
    sleep 2
    ./start_platform.sh
}

restart_backend() {
    echo "[$(date)] Reiniciando backend..." | tee -a "$LOG_FILE"
    ./stop_platform.sh
    sleep 2
    ./start_platform.sh
}

while true; do
    # Checar backend
    if ! curl -s "$BACKEND_HEALTH_URL" | grep 'healthy' >/dev/null; then
        echo "[$(date)] Backend fora do ar ou unhealthy" | tee -a "$LOG_FILE"
        restart_backend
        sleep 10
        continue
    fi

    # Checar frontend
    if check_port $FRONTEND_PORT && ! curl -s "$FRONTEND_URL" | grep -i '<!doctype html>' >/dev/null; then
        echo "[$(date)] Frontend porta $FRONTEND_PORT ocupada mas não responde corretamente" | tee -a "$LOG_FILE"
        restart_frontend
        sleep 10
        continue
    fi

    # Checar landing page
    if check_port $LANDING_PORT && ! curl -s "$LANDING_URL" | grep -i '<!doctype html>' >/dev/null; then
        echo "[$(date)] Landing page porta $LANDING_PORT ocupada mas não responde corretamente" | tee -a "$LOG_FILE"
        ./stop_platform.sh
        sleep 2
        ./start_platform.sh
        sleep 10
        continue
    fi

    echo "[$(date)] Stack saudável" | tee -a "$LOG_FILE"
    sleep 30

done
