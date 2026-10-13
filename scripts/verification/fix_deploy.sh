#!/bin/bash

# ClimateWise - Quick Deploy Fix Script
# Este script corrige problemas comuns de deploy

set -e

echo "🔧 ClimateWise - Script de Correção de Deploy"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Limpar builds anteriores
echo "1. Limpando builds anteriores..."
if [ -d "client/dist" ]; then
    rm -rf client/dist
    print_success "Build anterior removido"
else
    print_warning "Nenhum build anterior encontrado"
fi

# 2. Limpar node_modules e reinstalar
echo ""
echo "2. Reinstalando dependências do frontend..."
cd client
if [ -d "node_modules" ]; then
    rm -rf node_modules package-lock.json
fi
npm install
print_success "Dependências reinstaladas"

# 3. Fazer novo build
echo ""
echo "3. Fazendo novo build do frontend..."
npm run build
if [ $? -eq 0 ]; then
    print_success "Build completado com sucesso"
else
    print_error "Falha no build"
    exit 1
fi

# 4. Verificar arquivos gerados
echo ""
echo "4. Verificando arquivos gerados..."
if [ -f "dist/index.html" ]; then
    print_success "index.html gerado"
else
    print_error "index.html não encontrado"
    exit 1
fi

if [ -d "dist/assets" ]; then
    print_success "Assets gerados"
else
    print_error "Assets não encontrados"
    exit 1
fi

# 5. Testar servidor local
echo ""
echo "5. Testando servidor local..."
cd ..
if command -v python3 &> /dev/null; then
    echo "Iniciando servidor de teste em http://localhost:8888"
    echo "Pressione Ctrl+C para parar"
    cd client/dist && python3 -m http.server 8888
else
    print_warning "Python3 não encontrado, pulando teste de servidor local"
fi

print_success "Script de correção concluído!"
echo ""
echo "📝 Próximos passos:"
echo "  1. Para Netlify: Fazer push para GitHub e redeploy"
echo "  2. Para DigitalOcean: Executar ./deploy/deploy_digitalocean.sh"
echo ""
