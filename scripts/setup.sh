#!/bin/bash

# ============================================
# Script de Setup e Configuração do ClimateWise
# ============================================
# Este script configura automaticamente o ambiente
# ============================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 ClimateWise - Setup e Configuração Inicial"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running from project root
cd "$PROJECT_ROOT"

# Step 1: Check Python version
echo "1️⃣  Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python $PYTHON_VERSION encontrado"
else
    log_error "Python 3.9+ necessário"
    exit 1
fi

# Step 2: Check Node.js version
echo ""
echo "2️⃣  Verificando Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_info "Node.js $NODE_VERSION encontrado"
else
    log_warn "Node.js não encontrado (necessário para frontend)"
fi

# Step 3: Setup .env file
echo ""
echo "3️⃣  Configurando variáveis de ambiente..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_info "Arquivo .env criado a partir de .env.example"
        
        # Generate SECRET_KEY
        echo ""
        echo "Gerando SECRET_KEY segura..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        
        # Update SECRET_KEY in .env
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
        else
            # Linux
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
        fi
        
        log_info "SECRET_KEY gerada e configurada"
    else
        log_error ".env.example não encontrado"
        exit 1
    fi
else
    log_info "Arquivo .env já existe"
fi

# Step 4: Setup Python virtual environment
echo ""
echo "4️⃣  Configurando ambiente virtual Python..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    log_info "Ambiente virtual criado em .venv"
else
    log_info "Ambiente virtual já existe"
fi

# Activate virtual environment
source .venv/bin/activate
log_info "Ambiente virtual ativado"

# Step 5: Install Python dependencies
echo ""
echo "5️⃣  Instalando dependências Python..."
if [ -f "server/requirements-prod-ml.txt" ]; then
    pip install --upgrade pip
    pip install -r server/requirements-prod-ml.txt
    log_info "Dependências Python instaladas"
else
    log_error "requirements-prod-ml.txt não encontrado"
    exit 1
fi

# Step 6: Install Node.js dependencies
echo ""
echo "6️⃣  Instalando dependências Node.js..."
if [ -f "client/package.json" ]; then
    cd client
    npm install
    cd ..
    log_info "Dependências Node.js instaladas"
else
    log_warn "client/package.json não encontrado"
fi

# Step 7: Create necessary directories
echo ""
echo "7️⃣  Criando diretórios necessários..."
mkdir -p logs backups data .cache
log_info "Diretórios criados"

# Step 8: Setup database (if PostgreSQL available)
echo ""
echo "8️⃣  Verificando PostgreSQL..."
if command -v psql &> /dev/null; then
    log_info "PostgreSQL encontrado"
    # Database setup would go here
else
    log_warn "PostgreSQL não encontrado (necessário para produção)"
fi

# Step 9: Setup pre-commit hooks
echo ""
echo "9️⃣  Configurando pre-commit hooks..."
if [ -f ".pre-commit-config.yaml" ]; then
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        log_info "Pre-commit hooks instalados"
    else
        log_warn "pre-commit não instalado (pip install pre-commit)"
    fi
else
    log_warn ".pre-commit-config.yaml não encontrado"
fi

# Step 10: Final verification
echo ""
echo "🔍 Verificação final..."
echo ""

# Check critical files
CRITICAL_FILES=(
    ".env"
    "server/main.py"
    "client/package.json"
    "server/requirements-prod-ml.txt"
)

all_good=true
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_info "$file ✓"
    else
        log_error "$file ✗"
        all_good=false
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$all_good" = true ]; then
    echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Edite .env e configure suas chaves de API"
    echo "   2. Execute: ./start_platform.sh"
    echo "   3. Acesse: http://localhost:8000/docs"
else
    echo -e "${RED}❌ Setup incompleto. Verifique os erros acima.${NC}"
    exit 1
fi

echo ""
echo "📚 Documentação:"
echo "   - README.md"
echo "   - API_ENDPOINTS.md"
echo "   - ARCHITECTURE.md"
echo ""
