#!/bin/bash

# ============================================
# Quick Start - ClimateWise
# ============================================
# Inicialização rápida da plataforma
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 ClimateWise - Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Verify .env exists
echo "1️⃣  Verificando configuração..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env não encontrado. Criando...${NC}"
    cp .env.example .env
    
    # Generate SECRET_KEY
    echo "Gerando SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    else
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
    fi
    
    echo -e "${GREEN}✓ .env criado com SECRET_KEY segura${NC}"
else
    echo -e "${GREEN}✓ .env já existe${NC}"
fi

# Step 2: Verify Python environment
echo ""
echo "2️⃣  Verificando ambiente Python..."
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Criando ambiente virtual...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate
echo -e "${GREEN}✓ Ambiente virtual ativado${NC}"

# Step 3: Install Python dependencies
echo ""
echo "3️⃣  Instalando dependências Python..."
pip install -q --upgrade pip
if [ -f "server/requirements-prod-ml.txt" ]; then
    pip install -q -r server/requirements-prod-ml.txt
    echo -e "${GREEN}✓ Dependências Python instaladas${NC}"
else
    echo -e "${RED}✗ requirements-prod-ml.txt não encontrado${NC}"
    exit 1
fi

# Step 4: Install Node.js dependencies
echo ""
echo "4️⃣  Instalando dependências Node.js..."
if [ -f "client/package.json" ]; then
    cd client
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ Dependências Node.js instaladas${NC}"
else
    echo -e "${RED}✗ client/package.json não encontrado${NC}"
    exit 1
fi

# Step 5: Create necessary directories
echo ""
echo "5️⃣  Criando diretórios..."
mkdir -p backups logs data .cache
echo -e "${GREEN}✓ Diretórios criados${NC}"

# Step 6: Verify platform
echo ""
echo "6️⃣  Verificando plataforma..."
if [ -f "scripts/verify_platform.sh" ]; then
    ./scripts/verify_platform.sh || true
else
    echo -e "${YELLOW}⚠ Script de verificação não encontrado${NC}"
fi

# Step 7: Start platform
echo ""
echo "7️⃣  Iniciar plataforma?"
read -p "Deseja iniciar a plataforma agora? (s/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[SsYy]$ ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 URLs de Acesso"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "   Backend API:  http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
    echo "   Frontend:     http://localhost:3000"
    echo "   Landing Page: http://localhost:8080/landing-page.html"
    echo ""
    
    # Start backend
    echo "Iniciando backend..."
    (
        cd server
        PYTHONPATH=. python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ) &
    BACKEND_PID=$!
    echo -e "${GREEN}✓ Backend iniciado (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend
    echo "Aguardando backend inicializar..."
    sleep 5
    
    # Start frontend
    echo "Iniciando frontend..."
    (
        cd client
        npm run dev -- --host 0.0.0.0 --port 3000
    ) &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Frontend iniciado (PID: $FRONTEND_PID)${NC}"
    
    # Start landing page
    echo "Iniciando landing page..."
    python3 -m http.server 8080 --bind 0.0.0.0 &
    LANDING_PID=$!
    echo -e "${GREEN}✓ Landing Page iniciada (PID: $LANDING_PID)${NC}"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Plataforma iniciada com sucesso!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Para parar: ./stop_platform.sh"
    echo "Status:     ./status_platform.sh"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Setup concluído!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Para iniciar a plataforma:"
    echo "  ./start_platform.sh"
    echo ""
    echo "Para verificar status:"
    echo "  ./scripts/verify_platform.sh"
    echo ""
fi

echo "📚 Documentação:"
echo "   - README.md"
echo "   - DEPLOY_PRODUCTION.md"
echo "   - RELATORIO_FINAL_MELHORIAS.md"
echo ""
