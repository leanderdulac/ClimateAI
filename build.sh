#!/bin/bash
# Script para build otimizado das imagens Docker
# Uso: ./build.sh [production|development|all]

set -e

STAGE=${1:-production}
VERSION="1.0.0"
REGISTRY="climatewise"

echo "🐳 ClimateWise Docker Build Script"
echo "=================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

build_image() {
    local stage=$1
    local target_tag="$REGISTRY:$stage-v$VERSION"

    echo -e "${YELLOW}Building $stage image...${NC}"

    docker build \
        --target=$stage \
        --tag "$target_tag" \
        --label "version=$VERSION" \
        --label "stage=$stage" \
        --progress=plain \
        ./server

    echo -e "${GREEN}✓ $stage image built successfully!${NC}"
    echo "   Image: $target_tag"
    echo "   Size: $(docker images $target_tag --format='{{.Size}}')"
}

show_help() {
    cat << EOF
Usage: ./build.sh [STAGE]

Stages:
  production   - Imagem otimizada para produção (~500MB)
  development  - Imagem com TensorFlow para dev (~2GB)
  all          - Build ambos os stages

Examples:
  ./build.sh production
  ./build.sh development
  ./build.sh all

Notes:
  - Production usa requirements-base.txt
  - Development usa requirements-base.txt + requirements-ml.txt
  - Multi-stage build apenas inclui necessário em cada stage

EOF
}

case $STAGE in
    production)
        build_image "production"
        ;;
    development)
        build_image "development"
        ;;
    all)
        build_image "production"
        echo ""
        build_image "development"
        echo ""
        echo -e "${GREEN}Size Comparison:${NC}"
        docker images "$REGISTRY:*" --format='table {{.Tag}}\t{{.Size}}'
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown stage: $STAGE${NC}"
        show_help
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Build completed!${NC}"
