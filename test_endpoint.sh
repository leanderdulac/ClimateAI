#!/bin/bash
cd /home/artha/climateAI/server
source venv/bin/activate
python main.py &
SERVER_PID=$!
sleep 5

echo "Testando endpoint de previsão..."
curl -X GET "http://localhost:8000/api/clima/previsao?latitude=-23.5505&longitude=-46.6333&dias=7" -H "Content-Type: application/json" || echo "Falhou"

echo "Matando servidor..."
kill $SERVER_PID