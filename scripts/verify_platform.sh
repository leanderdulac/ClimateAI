#!/bin/bash

# ============================================
# Script de Verificação Completa do ClimateWise
# ============================================
# Verifica todos os componentes da plataforma
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
PASS=0
FAIL=0
WARN=0

# Functions
log_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    ((FAIL++))
}

log_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
    ((WARN++))
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 ClimateWise - Verificação Completa"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Verificar Python
echo "1️⃣  Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_pass "Python $PYTHON_VERSION instalado"
else
    log_fail "Python 3 não encontrado"
fi

# 2. Verificar Node.js
echo ""
echo "2️⃣  Verificando Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_pass "Node.js $NODE_VERSION instalado"
else
    log_warn "Node.js não encontrado (necessário para frontend)"
fi

# 3. Verificar arquivos de configuração
echo ""
echo "3️⃣  Verificando arquivos de configuração..."

CONFIG_FILES=(
    ".env.example"
    "server/config/config.py"
    "server/requirements-prod-ml.txt"
    "client/package.json"
    "docker-compose.yml"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_pass "$file existe"
    else
        log_fail "$file não encontrado"
    fi
done

# 4. Verificar .env
echo ""
echo "4️⃣  Verificando .env..."
if [ -f ".env" ]; then
    log_pass ".env existe"
    
    # Verificar SECRET_KEY
    if grep -q "^SECRET_KEY=." .env; then
        SECRET_KEY_LENGTH=$(grep "^SECRET_KEY=" .env | cut -d'=' -f2 | wc -c)
        if [ "$SECRET_KEY_LENGTH" -gt 32 ]; then
            log_pass "SECRET_KEY configurada e segura"
        else
            log_fail "SECRET_KEY muito curta (< 32 caracteres)"
        fi
    else
        log_fail "SECRET_KEY não configurada no .env"
    fi
    
    # Verificar DATABASE_URL
    if grep -q "^DATABASE_URL=" .env; then
        log_pass "DATABASE_URL configurada"
    else
        log_warn "DATABASE_URL não configurada (usando padrão)"
    fi
else
    log_warn ".env não existe (criar a partir de .env.example)"
fi

# 5. Verificar ambiente virtual Python
echo ""
echo "5️⃣  Verificando ambiente virtual Python..."
if [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
    log_pass "Ambiente virtual Python existe"
    
    # Verificar se está ativado
    if [ -n "$VIRTUAL_ENV" ]; then
        log_pass "Ambiente virtual ativado"
    else
        log_warn "Ambiente virtual não ativado"
    fi
else
    log_warn "Ambiente virtual não encontrado"
fi

# 6. Verificar dependências Python
echo ""
echo "6️⃣  Verificando dependências Python..."
if [ -f ".venv/bin/pip" ]; then
    .venv/bin/pip check > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_pass "Dependências Python instaladas e consistentes"
    else
        log_warn "Conflitos nas dependências Python"
    fi
else
    log_warn "pip não encontrado no .venv"
fi

# 7. Verificar dependências Node.js
echo ""
echo "7️⃣  Verificando dependências Node.js..."
if [ -d "client/node_modules" ]; then
    log_pass "Dependências Node.js instaladas"
else
    log_warn "node_modules não encontrado (rodar npm install)"
fi

# 8. Verificar PostgreSQL
echo ""
echo "8️⃣  Verificando PostgreSQL..."
if command -v psql &> /dev/null; then
    log_pass "PostgreSQL instalado"
    
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log_pass "PostgreSQL rodando"
    else
        log_warn "PostgreSQL não está rodando"
    fi
else
    log_warn "PostgreSQL não instalado"
fi

# 9. Verificar Redis
echo ""
echo "9️⃣  Verificando Redis..."
if command -v redis-cli &> /dev/null; then
    log_pass "Redis instalado"
    
    if redis-cli ping > /dev/null 2>&1; then
        log_pass "Redis rodando"
    else
        log_warn "Redis não está rodando"
    fi
else
    log_warn "Redis não instalado"
fi

# 10. Verificar scripts
echo ""
echo "🔧 Verificando scripts..."

SCRIPTS=(
    "scripts/setup.sh"
    "scripts/backup.sh"
    "scripts/restore.sh"
    "scripts/generate_secret_key.sh"
    "start_platform.sh"
    "stop_platform.sh"
    "status_platform.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        log_pass "$script existe e é executável"
    elif [ -f "$script" ]; then
        log_warn "$script existe mas não é executável"
    else
        log_fail "$script não encontrado"
    fi
done

# 11. Verificar estrutura de diretórios
echo ""
echo "📁 Verificando estrutura de diretórios..."

DIRS=(
    "server"
    "client"
    "server/api"
    "server/services"
    "server/tests"
    "client/src"
    "client/tests"
    "backups"
    "logs"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_pass "Diretório $dir existe"
    else
        log_warn "Diretório $dir não existe"
        mkdir -p "$dir"
        log_info "Criado: $dir"
    fi
done

# 12. Verificar testes
echo ""
echo "🧪 Verificando testes..."

TEST_FILES=(
    "server/tests/unit/test_config.py"
    "server/tests/unit/test_auth_service.py"
    "server/tests/integration/test_api_integration.py"
)

for test in "${TEST_FILES[@]}"; do
    if [ -f "$test" ]; then
        log_pass "$test existe"
    else
        log_warn "$test não encontrado"
    fi
done

# 13. Verificar documentação
echo ""
echo "📚 Verificando documentação..."

DOCS=(
    "README.md"
    "API_ENDPOINTS.md"
    "ARCHITECTURE.md"
    "CONTRIBUTING.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        log_pass "$doc existe"
    else
        log_warn "$doc não encontrado"
    fi
done

# 14. Verificar Docker
echo ""
echo "🐳 Verificando Docker..."
if command -v docker &> /dev/null; then
    log_pass "Docker instalado"
    
    if command -v docker-compose &> /dev/null; then
        log_pass "Docker Compose instalado"
    else
        log_warn "Docker Compose não encontrado"
    fi
    
    if docker ps > /dev/null 2>&1; then
        log_pass "Docker daemon rodando"
    else
        log_warn "Docker daemon não está rodando"
    fi
else
    log_warn "Docker não instalado"
fi

# 15. Verificar Git
echo ""
echo "🔖 Verificando Git..."
if command -v git &> /dev/null; then
    log_pass "Git instalado"
    
    if [ -d ".git" ]; then
        log_pass "Repositório Git inicializado"
        
        BRANCH=$(git branch --show-current)
        log_info "Branch atual: $BRANCH"
    else
        log_warn "Não é um repositório Git"
    fi
else
    log_warn "Git não instalado"
fi

# Resumo final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumo da Verificação"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Aprovados:${NC}  $PASS"
echo -e "${RED}✗ Falhos:${NC}    $FAIL"
echo -e "${YELLOW}⚠ Alertas:${NC}   $WARN"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -le 5 ]; then
    echo -e "${GREEN}✅ Plataforma está pronta para uso!${NC}"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Configure suas chaves de API no .env"
    echo "   2. Execute: ./start_platform.sh"
    echo "   3. Acesse: http://localhost:8000/docs"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Plataforma funcional com alertas${NC}"
    echo ""
    echo "Revise os alertas acima e corrija se necessário"
    exit 0
else
    echo -e "${RED}❌ Plataforma com problemas críticos${NC}"
    echo ""
    echo "Corrija os erros listados acima antes de continuar"
    exit 1
fi
