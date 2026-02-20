#!/bin/bash
# Script de monitoramento contínuo dos endpoints de localização
# Salva logs e alerta se algum endpoint falhar

LOG_FILE="monitor_localizacao.log"
BASE_URL="http://localhost:8000/api/v1/localizacao"

while true; do
    echo "[$(date)] Testando endpoints de localização..." | tee -a "$LOG_FILE"
    # Testar CEP
    CEP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/cep/29010001")
    if [ "$CEP_STATUS" != "200" ]; then
        echo "[$(date)] Falha no endpoint CEP: $CEP_STATUS" | tee -a "$LOG_FILE"
    fi
    # Testar cidade
    CITY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/cidade/Vitória")
    if [ "$CITY_STATUS" != "200" ]; then
        echo "[$(date)] Falha no endpoint cidade: $CITY_STATUS" | tee -a "$LOG_FILE"
    fi
    # Testar reverse geocode
    REV_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/coordenadas?latitude=-20.3155&longitude=-40.3128")
    if [ "$REV_STATUS" != "200" ]; then
        echo "[$(date)] Falha no endpoint reverse geocode: $REV_STATUS" | tee -a "$LOG_FILE"
    fi
    echo "[$(date)] Monitoramento concluído." | tee -a "$LOG_FILE"
    sleep 60
done
