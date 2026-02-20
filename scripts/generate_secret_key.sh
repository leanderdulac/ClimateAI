#!/bin/bash

# ============================================
# Script para gerar SECRET_KEY segura
# ============================================

echo "🔐 Gerando SECRET_KEY segura..."
echo ""

# Generate secure key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "✅ SECRET_KEY gerada com sucesso!"
echo ""
echo "Adicione ao seu arquivo .env:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SECRET_KEY=${SECRET_KEY}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ask if user wants to update .env file
if [ -f ".env" ]; then
    read -p "Deseja atualizar o arquivo .env automaticamente? (s/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        # Backup existing .env
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ Backup criado: .env.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update or add SECRET_KEY
        if grep -q "^SECRET_KEY=" .env; then
            # Replace existing
            sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
            echo "✅ SECRET_KEY atualizada no .env"
        else
            # Add new
            echo "SECRET_KEY=${SECRET_KEY}" >> .env
            echo "✅ SECRET_KEY adicionada ao .env"
        fi
    fi
else
    echo "⚠️  Arquivo .env não encontrado."
    echo "Crie um arquivo .env baseado em .env.example"
    echo ""
    echo "Comando: cp .env.example .env"
fi

echo ""
echo "📋 Informações de segurança:"
echo "  - Tamanho da chave: ${#SECRET_KEY} caracteres"
echo "  - Formato: URL-safe base64"
echo "  - Entropia: 256 bits"
echo ""
echo "⚠️  NUNCA commit o arquivo .env no Git!"
