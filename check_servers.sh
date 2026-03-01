#!/bin/bash
# Script de verificação completa do ClimateWise

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ClimateWise - Verificação Completa de Servidores         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function check_port() {
    local port=$1
    local name=$2
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name (porta $port) - OK"
        return 0
    else
        echo -e "${RED}✗${NC} $name (porta $port) - NÃO RESPONDENDO"
        return 1
    fi
}

function check_http() {
    local url=$1
    local name=$2
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} $name - HTTP $response"
        return 0
    else
        echo -e "${RED}✗${NC} $name - HTTP $response"
        return 1
    fi
}

echo "1. VERIFICANDO PORTAS"
echo "────────────────────────────────────────────────────────────"
check_port 8000 "Backend"
check_port 5173 "Frontend (Vite)"
echo ""

echo "2. VERIFICANDO ENDPOINTS HTTP"
echo "────────────────────────────────────────────────────────────"
check_http "http://localhost:8000/health" "Backend Health"
check_http "http://localhost:8000/docs" "Swagger UI"
check_http "http://localhost:5173/" "Frontend Home"
check_http "http://localhost:5173/api/v1/atlas-integration/health" "Atlas Integration"
echo ""

echo "3. PROCESSOS RODANDO"
echo "────────────────────────────────────────────────────────────"
ps aux | grep -E "uvicorn.*main:app|vite" | grep -v grep | while read line; do
    echo "  • ${line:0:100}"
done
echo ""

echo "4. LOGS RECENTES"
echo "────────────────────────────────────────────────────────────"
echo "Backend (últimas 5 linhas):"
tail -5 /tmp/climatewise_server.log 2>/dev/null | sed 's/^/  /' || echo "  Sem logs disponíveis"
echo ""
echo "Frontend (últimas 5 linhas):"
tail -5 /tmp/climatewise_frontend.log 2>/dev/null | sed 's/^/  /' || echo "  Sem logs disponíveis"
echo ""

echo "5. ENDEREÇOS DE ACESSO"
echo "────────────────────────────────────────────────────────────"
echo -e "${GREEN}✓${NC} Frontend:  http://localhost:5173"
echo -e "${GREEN}✓${NC} Backend:   http://localhost:8000"
echo -e "${GREEN}✓${NC} Swagger:   http://localhost:8000/docs"
echo -e "${GREEN}✓${NC} ReDoc:     http://localhost:8000/redoc"
echo -e "${GREEN}✓${NC} Atlas:     http://localhost:8000/api/v1/atlas-integration/health"
echo ""

echo "6. DIAGNÓSTICO TELA BRANCA"
echo "────────────────────────────────────────────────────────────"
echo "Verificando se o index.html está sendo servido..."
if curl -s http://localhost:5173/ | grep -q "root"; then
    echo -e "${GREEN}✓${NC} index.html está sendo servido corretamente"
else
    echo -e "${RED}✗${NC} Problema ao servir index.html"
fi

echo ""
echo "Verificando bundle JavaScript..."
if curl -s http://localhost:5173/ | grep -q "script type"; then
    echo -e "${GREEN}✓${NC} Scripts JavaScript estão presentes"
else
    echo -e "${YELLOW}⚠${NC} Scripts JavaScript podem estar faltando"
fi

echo ""
echo "Verificando conexão com API do frontend..."
API_RESPONSE=$(curl -s http://localhost:5173/api/v1/atlas-integration/health 2>/dev/null)
if echo "$API_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC} Frontend consegue conectar ao backend"
else
    echo -e "${RED}✗${NC} Frontend NÃO consegue conectar ao backend"
    echo "  Verifique o proxy do Vite em vite.config.ts"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  POSSÍVEIS CAUSAS DA TELA BRANCA                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  1. Erros no console do navegador (F12)                 ║"
echo "║  2. Cache antigo do navegador (Ctrl+Shift+R)            ║"
echo "║  3. Erros de importação de módulos React                ║"
echo "║  4. Variáveis de ambiente faltando (.env)               ║"
echo "║  5. Erros de TypeScript na compilação                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "7. AÇÕES RECOMENDADAS"
echo "────────────────────────────────────────────────────────────"
echo "1. Abra o navegador em: http://localhost:5173"
echo "2. Pressione F12 para abrir DevTools"
echo "3. Verifique a aba 'Console' por erros"
echo "4. Verifique a aba 'Network' por falhas de carregamento"
echo "5. Tente limpar cache: Ctrl+Shift+R (Linux) ou Cmd+Shift+R (Mac)"
echo ""
echo "Se persistir, execute:"
echo "  cd client && npm run dev -- --force"
echo ""
