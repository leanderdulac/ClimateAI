#!/bin/bash

# Script para iniciar o servidor da landing page do ClimateAI

echo "🚀 Iniciando servidor da Landing Page do ClimateAI..."
echo "📍 URL: http://localhost:8080"
echo "📱 Acesse a partir de qualquer dispositivo na rede"

# Inicia um servidor HTTP simples na porta 8080
cd /home/artha/climateAI
python3 -m http.server 8080

echo "✅ Servidor parado"