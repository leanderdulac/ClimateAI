#!/bin/bash
# Script de inicialização do ClimateWise - FIMCE

echo "Iniciando o ClimateWise - Framework Integrado de Modelagem Climático-Econômica (FIMCE)"

# Iniciar o backend
echo "Iniciando o backend..."
cd /home/artha/climateAI/server
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

BACKEND_PID=$!
echo "Backend iniciado com PID: $BACKEND_PID"

# Iniciar o frontend (em outro terminal)
echo "Para iniciar o frontend, execute em outro terminal:"
echo "cd /home/artha/climateAI/client && npm run dev"

echo "Backend disponível em: http://localhost:8000"
echo "Documentação da API disponível em: http://localhost:8000/docs"

# Para parar o backend: kill $BACKEND_PID
