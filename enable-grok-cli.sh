#!/bin/bash
# Script para garantir que o grok-cli esteja disponível no terminal

# Descobre os diretórios globais de binários do npm e bun
echo "Detectando diretórios globais de binários..."
NPM_BIN=$(npm bin -g)
BUN_BIN="$HOME/.bun/bin"

# Adiciona ao PATH se não estiver
if [[ ":$PATH:" != *":$NPM_BIN:"* ]]; then
    export PATH="$NPM_BIN:$PATH"
    echo "Adicionado $NPM_BIN ao PATH."
fi
if [[ ":$PATH:" != *":$BUN_BIN:"* ]]; then
    export PATH="$BUN_BIN:$PATH"
    echo "Adicionado $BUN_BIN ao PATH."
fi

# Sugere adicionar ao ~/.bashrc para tornar permanente
echo "Para tornar permanente, execute:"
echo "echo 'export PATH=\"$NPM_BIN:$BUN_BIN:$PATH\"' >> ~/.bashrc && source ~/.bashrc"

# Testa o grok-cli
grok --help || echo "grok-cli não encontrado. Verifique se foi instalado corretamente via npm ou bun."
