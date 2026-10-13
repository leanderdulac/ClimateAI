#!/usr/bin/env bash
# ==============================================================================
# ClimateWise - Akash Network Inference Deployment Helper
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDL_GPU="${SCRIPT_DIR}/deploy-inference.yaml"
SDL_CPU="${SCRIPT_DIR}/deploy-inference-cpu.yaml"

MODE="${1:-gpu}"

echo "========================================================================"
echo " ClimateWise AI - Akash Network Inference Deployment"
echo "========================================================================"

if [ "$MODE" = "cpu" ]; then
    SDL_FILE="$SDL_CPU"
    echo "Selecionado: Modo CPU Econômico ($SDL_FILE)"
else
    SDL_FILE="$SDL_GPU"
    echo "Selecionado: Modo GPU de Alta Performance ($SDL_FILE)"
fi

if ! command -v akash &> /dev/null; then
    echo "AVISO: O binário 'akash' CLI não foi detectado no PATH."
    echo "Para implantar via Akash Console Web (Recomendado):"
    echo "  1. Acesse: https://console.akash.network"
    echo "  2. Conecte sua carteira (Keplr / Leap / MetaMask) ou use sua API Key."
    echo "  3. Crie um novo Deployment e cole o conteúdo do arquivo:"
    echo "     $SDL_FILE"
    echo "  4. Após o provisionamento, copie a URL gerada e configure em seu .env:"
    echo "     INFERENCE_SERVICE_URL=https://<provedor-akash-url>"
    exit 0
fi

echo "Validando sintaxe do manifesto SDL..."
if [ -f "$SDL_FILE" ]; then
    echo "SDL válido encontrado: $SDL_FILE"
else
    echo "ERRO: Arquivo SDL não encontrado em $SDL_FILE"
    exit 1
fi

echo ""
echo "Instruções com Akash CLI:"
echo "  akash tx deployment create $SDL_FILE --from <sua-carteira> --gas-prices 0.025uakt -y"
echo ""
