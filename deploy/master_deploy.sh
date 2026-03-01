#!/bin/bash

# ClimateWise - Master Deployment Script
# Orchestrates Frontend (Vercel), Backend (GCP), and Blockchain deployment.

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}       ClimateWise - Master Deployment Orchestrator           ${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo "Este script irá guiá-lo através dos 5 passos de deploy."
echo "Certifique-se de estar logado no gcloud e ter acesso à Vercel."
echo ""

# Check Prerequisites
check_command() {
    if ! command -v $1 &> /dev/null;
    then
        echo -e "${RED}Erro: $1 não está instalado.${NC}"
        exit 1
    fi
}

check_command gcloud
check_command npm
check_command python3

# ==============================================================================
# PASSO 1: Deploy do Frontend na Vercel
# ==============================================================================
echo -e "${YELLOW}>> [1/5] Iniciando Deploy do Frontend (Vercel)...${NC}"
read -p "Deseja realizar o deploy do Frontend agora? (y/n): " do_frontend

FRONTEND_URL=""

if [[ "$do_frontend" == "y" ]]; then
    cd ../client
    echo "Instalando dependências do frontend..."
    npm install
    
    echo "Iniciando deploy Vercel..."
    # npx vercel deploy --prod triggers login flow if needed
    npx vercel deploy --prod > vercel_output.txt 2>&1
    
    # Extract URL (simplified logic, user might need to verify)
    # Usually vercel output contains the url. 
    # For interactive script, simpler to ask user or assume they see it.
    cat vercel_output.txt
    echo ""
    echo -e "${GREEN}Deploy Frontend concluído (verifique saída acima).${NC}"
    read -p "Cole a URL final do Frontend (ex: https://climatewise.vercel.app): " FRONTEND_URL
    cd ../deploy
else
    read -p "Insira a URL do Frontend existente (para configurar CORS no backend): " FRONTEND_URL
fi

# ==============================================================================
# PASSO 2: Deploy do Backend no Google Cloud Run
# ==============================================================================
echo -e "${YELLOW}>> [2/5] Iniciando Deploy do Backend (Google Cloud Run)...${NC}"
read -p "Deseja realizar o deploy do Backend agora? (y/n): " do_backend

BACKEND_SERVICE_NAME="climatewise-backend"
REGION="us-central1"

if [[ "$do_backend" == "y" ]]; then
    # Run the dedicated GCP deploy script
    ./deploy_gcp.sh
    
    echo ""
    echo -e "${GREEN}Backend Deploy concluído.${NC}"
else
    echo "Pulando deploy do backend..."
fi

# ==============================================================================
# PASSO 3: Configurar CORS
# ==============================================================================
echo -e "${YELLOW}>> [3/5] Configurando CORS no Backend...${NC}"

if [[ -n "$FRONTEND_URL" ]]; then
    echo "Configurando ALLOW_ORIGINS=$FRONTEND_URL no Cloud Run..."
    gcloud run services update $BACKEND_SERVICE_NAME \
        --update-env-vars ALLOW_ORIGINS="$FRONTEND_URL" \
        --region $REGION \
        --platform managed
    echo -e "${GREEN}CORS configurado com sucesso!${NC}"
else
    echo -e "${RED}URL do Frontend não fornecida. Pulando configuração de CORS.${NC}"
fi

# ==============================================================================
# PASSO 4: Deploy do Contrato Blockchain
# ==============================================================================
echo -e "${YELLOW}>> [4/5] Deploy do Contrato Inteligente (Blockchain)...${NC}"
echo "Você precisará de uma URL RPC (ex: Sepolia) e uma Chave Privada com fundos."
read -p "Deseja realizar o deploy do contrato agora? (y/n): " do_contract

CONTRACT_ADDRESS=""
CONTRACT_ABI=""

if [[ "$do_contract" == "y" ]]; then
    read -p "Digite a BC_NODE_URL (RPC): " BC_NODE_URL
    read -s -p "Digite a PRIVATE_KEY (Deployer): " PRIVATE_KEY
    echo ""
    
    export BC_NODE_URL=$BC_NODE_URL
    export PRIVATE_KEY=$PRIVATE_KEY
    
    # Install python deps if needed
    # pip install -r ../server/requirements-base.txt
    
    echo "Executando script de deploy..."
    cd ../server
    python3 scripts/deploy_tokenization.py > deploy_output.txt
    
    cat deploy_output.txt
    
    # Try to extract address from log (simplified)
    CONTRACT_ADDRESS=$(grep "Contract Address:" deploy_output.txt | cut -d ':' -f 2 | xargs)
    cd ../deploy
    
    if [[ -n "$CONTRACT_ADDRESS" ]]; then
        echo -e "${GREEN}Contrato deployado em: $CONTRACT_ADDRESS${NC}"
    else
        echo -e "${RED}Não foi possível capturar o endereço do contrato automaticamente.${NC}"
        read -p "Cole o endereço do contrato manualmente: " CONTRACT_ADDRESS
    fi
else
    echo "Pulando deploy do contrato..."
fi

# ==============================================================================
# PASSO 5: Atualizar Backend com Endereço do Contrato
# ==============================================================================
echo -e "${YELLOW}>> [5/5] Atualizando Backend com configurações Blockchain...${NC}"

if [[ -n "$CONTRACT_ADDRESS" ]]; then
    echo "Atualizando variáveis de ambiente no Cloud Run..."
    
    # Note: For ABI, it's complex to pass JSON via CLI flags sometimes. 
    # Usually better to use Secret Manager, but here we set basic vars.
    
    gcloud run services update $BACKEND_SERVICE_NAME \
        --update-env-vars BLOCKCHAIN_ENABLED="True" \
        --update-env-vars CONTRACT_ADDRESS="$CONTRACT_ADDRESS" \
        --update-env-vars BC_NODE_URL="$BC_NODE_URL" \
        --region $REGION \
        --platform managed
        
    echo -e "${GREEN}Backend atualizado com sucesso!${NC}"
else
    echo "Endereço do contrato não disponível. Pule este passo."
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}       Processo Finalizado!           ${NC}"
echo -e "${BLUE}============================================================${NC}"
