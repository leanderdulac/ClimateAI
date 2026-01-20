#!/bin/bash

# Script para iniciar o servidor da landing page do ClimateAI

echo "🚀 Iniciando servidor da Landing Page do ClimateAI..."
echo "📍 URL: http://localhost:8080/landing-page.html"
echo "📱 Acesse a partir de qualquer dispositivo na rede"
echo ""
echo "Para parar o servidor, pressione Ctrl+C"
echo ""

# Verifica se o arquivo existe
if [ ! -f "landing-page.html" ]; then
    echo "❌ Erro: Arquivo landing-page.html não encontrado!"
    exit 1
fi

# Inicia um servidor HTTP simples na porta 8080
cd /home/artha/climateAI
python3 -m http.server 8080 --bind 0.0.0.0

echo ""
echo "✅ Servidor parado"
