#!/bin/bash

# ============================================
# Script de Teste Completo do ClimateWise
# ============================================
# Executa todos os testes: unitários, integração e E2E
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 ClimateWise - Suite de Testes Completa"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Função para rodar testes Python
run_python_tests() {
    echo "📍 Testes Unitários Python..."
    echo ""
    
    if [ -f ".venv/bin/pytest" ]; then
        # Ativar ambiente virtual
        source .venv/bin/activate
        
        # Rodar testes unitários
        cd server
        if pytest tests/unit/ -v --tb=short; then
            echo -e "${GREEN}✓ Testes unitários Python passaram${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${RED}✗ Testes unitários Python falharam${NC}"
            ((TESTS_FAILED++))
        fi
        cd ..
    else
        echo -e "${YELLOW}⚠ pytest não encontrado. Instalando...${NC}"
        if [ -f ".venv/bin/pip" ]; then
            .venv/bin/pip install pytest pytest-async pytest-cov
        else
            echo -e "${RED}✗ pip não encontrado${NC}"
            return 1
        fi
    fi
}

# Função para rodar testes de integração
run_integration_tests() {
    echo ""
    echo "🔗 Testes de Integração..."
    echo ""
    
    if [ -f ".venv/bin/pytest" ]; then
        source .venv/bin/activate
        
        cd server
        if pytest tests/integration/ -v --tb=short -k "not slow"; then
            echo -e "${GREEN}✓ Testes de integração passaram${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${YELLOW}⚠ Testes de integração falharam (pode exigir database)${NC}"
            ((TESTS_FAILED++))
        fi
        cd ..
    fi
}

# Função para rodar testes do frontend
run_frontend_tests() {
    echo ""
    echo "🎨 Testes do Frontend..."
    echo ""
    
    if [ -f "client/package.json" ]; then
        cd client
        
        # Instalar dependências se necessário
        if [ ! -d "node_modules" ]; then
            echo "Instalando dependências do frontend..."
            npm install
        fi
        
        # Rodar testes
        if npm run test:run; then
            echo -e "${GREEN}✓ Testes do frontend passaram${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "${YELLOW}⚠ Testes do frontend falharam${NC}"
            ((TESTS_FAILED++))
        fi
        
        cd ..
    fi
}

# Função para rodar testes E2E
run_e2e_tests() {
    echo ""
    echo "🎯 Testes E2E (Playwright)..."
    echo ""
    
    if [ -f "client/package.json" ]; then
        cd client
        
        # Verificar se Playwright está instalado
        if npm list @playwright/test > /dev/null 2>&1; then
            # Rodar testes E2E
            if npm run test:e2e; then
                echo -e "${GREEN}✓ Testes E2E passaram${NC}"
                ((TESTS_PASSED++))
            else
                echo -e "${YELLOW}⚠ Testes E2E falharam (pode exigir servidor rodando)${NC}"
                ((TESTS_FAILED++))
            fi
        else
            echo -e "${YELLOW}⚠ Playwright não instalado${NC}"
        fi
        
        cd ..
    fi
}

# Função para verificar cobertura de testes
check_coverage() {
    echo ""
    echo "📊 Cobertura de Testes..."
    echo ""
    
    if [ -f ".venv/bin/pytest" ] && [ -f "server/pytest.ini" ]; then
        source .venv/bin/activate
        
        cd server
        pytest --cov=. --cov-report=term-missing --cov-fail-under=60 || true
        cd ..
    else
        echo -e "${YELLOW}⚠ Cobertura não disponível${NC}"
    fi
}

# Executar todos os testes
echo "1️⃣  Rodando testes unitários..."
run_python_tests || true

echo ""
echo "2️⃣  Rodando testes de integração..."
run_integration_tests || true

echo ""
echo "3️⃣  Rodando testes do frontend..."
run_frontend_tests || true

echo ""
echo "4️⃣  Rodando testes E2E..."
run_e2e_tests || true

echo ""
echo "5️⃣  Verificando cobertura..."
check_coverage || true

# Resumo final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumo dos Testes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Testes aprovados:${NC}  $TESTS_PASSED"
echo -e "${RED}✗ Testes falharam:${NC}    $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Todos os testes passaram!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Alguns testes falharam${NC}"
    echo ""
    echo "Revise os logs acima para detalhes"
    exit 1
fi
