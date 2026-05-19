#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_SYSTEM=1
INSTALL_OPTIONAL=0
SKIP_PLAYWRIGHT=0
REFRESH_ENV=0
VALIDATE_COMPOSE=0

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap_environment.sh [options]

Options:
  --skip-system        Skip apt/system package installation
  --with-optional      Also install optional Python requirements (ML and Atlas)
  --skip-playwright    Skip Playwright browser installation
  --refresh-env        Update an existing .env with generated local defaults
  --validate-compose   Validate docker compose files when daemon is accessible
  -h, --help           Show this help
EOF
}

log_info() {
  echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
  echo -e "${RED}✗${NC} $1"
}

generate_secret() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
}

set_env_value() {
  local env_file="$1"
  local key="$2"
  local value="$3"

  if grep -qE "^${key}=" "$env_file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$env_file"
  fi
}

install_system_packages() {
  local missing=()
  local packages=(
    docker.io
    docker-compose-v2
    podman
    podman-compose
    ripgrep
    python-is-python3
    python3-venv
    python3-pip
    curl
    git
    lsof
  )

  for pkg in "${packages[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
      missing+=("$pkg")
    fi
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    log_info "Pacotes de sistema já instalados"
    return
  fi

  if ! command -v sudo >/dev/null 2>&1; then
    log_warn "sudo não encontrado; pulando instalação de pacotes do sistema"
    return
  fi

  echo -e "${BLUE}Instalando pacotes do sistema...${NC}"
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"

  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl enable --now docker >/dev/null 2>&1 || log_warn "Não foi possível habilitar o serviço docker automaticamente"
  fi

  if getent group docker >/dev/null 2>&1 && ! id -nG | grep -qw docker; then
    sudo usermod -aG docker "$USER" || log_warn "Não foi possível adicionar $USER ao grupo docker"
    log_warn "Abra um novo shell ou execute 'newgrp docker' para usar o Docker sem sudo"
  fi
}

prepare_env_file() {
  local env_file="$PROJECT_ROOT/.env"
  local created_env=0

  if [[ ! -f "$env_file" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$env_file"
    log_info ".env criado a partir de .env.example"
    created_env=1
  else
    log_info ".env já existe"
  fi

  if [[ $created_env -eq 1 || $REFRESH_ENV -eq 1 ]]; then
    set_env_value "$env_file" "SECRET_KEY" "${SECRET_KEY:-$(generate_secret)}"
    set_env_value "$env_file" "GRAFANA_ADMIN_PASSWORD" "${GRAFANA_ADMIN_PASSWORD:-$(generate_secret)}"
    set_env_value "$env_file" "POSTGRES_USER" "${POSTGRES_USER:-climatewise}"
    set_env_value "$env_file" "POSTGRES_DB" "${POSTGRES_DB:-climatewise}"
    set_env_value "$env_file" "POSTGRES_PASSWORD" "${POSTGRES_PASSWORD:-$(generate_secret)}"
    set_env_value "$env_file" "JUPYTER_TOKEN" "${JUPYTER_TOKEN:-$(generate_secret)}"
    set_env_value "$env_file" "ALLOW_ORIGINS" "${ALLOW_ORIGINS:-http://localhost:3000,http://localhost:5173,http://localhost:8080}"
    log_info "Variáveis essenciais de ambiente preparadas em .env"
  else
    log_warn ".env existente preservado; use --refresh-env para reescrever defaults locais"
  fi
}

setup_python() {
  echo -e "${BLUE}Configurando ambiente Python...${NC}"

  if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
    python3 -m venv "$PROJECT_ROOT/.venv"
    log_info "Ambiente virtual .venv criado"
  fi

  "$PROJECT_ROOT/.venv/bin/python" -m pip install --upgrade pip setuptools wheel
  "$PROJECT_ROOT/.venv/bin/python" -m pip install -r "$PROJECT_ROOT/server/requirements.txt"

  if [[ $INSTALL_OPTIONAL -eq 1 ]]; then
    [[ -f "$PROJECT_ROOT/server/requirements-ml.txt" ]] && "$PROJECT_ROOT/.venv/bin/python" -m pip install -r "$PROJECT_ROOT/server/requirements-ml.txt"
    [[ -f "$PROJECT_ROOT/server/requirements-atlas.txt" ]] && "$PROJECT_ROOT/.venv/bin/python" -m pip install -r "$PROJECT_ROOT/server/requirements-atlas.txt"
  fi

  log_info "Dependências Python instaladas"
}

setup_node() {
  echo -e "${BLUE}Configurando dependências Node.js...${NC}"

  if ! command -v npm >/dev/null 2>&1; then
    log_warn "npm não encontrado; pulando dependências Node.js"
    return
  fi

  if [[ -f "$PROJECT_ROOT/package-lock.json" ]]; then
    (cd "$PROJECT_ROOT" && npm ci)
  else
    (cd "$PROJECT_ROOT" && npm install)
  fi

  if [[ -f "$PROJECT_ROOT/client/package-lock.json" ]]; then
    (cd "$PROJECT_ROOT/client" && npm ci)
  else
    (cd "$PROJECT_ROOT/client" && npm install)
  fi

  if [[ $SKIP_PLAYWRIGHT -eq 0 ]]; then
    (cd "$PROJECT_ROOT/client" && npx playwright install --with-deps chromium firefox webkit) || log_warn "Falha ao instalar navegadores do Playwright; use os scripts *:local se necessário"
  fi

  log_info "Dependências Node.js instaladas"
}

run_validations() {
  echo -e "${BLUE}Executando validações rápidas...${NC}"

  (cd "$PROJECT_ROOT" && PYTHONPATH=server:. ./.venv/bin/pytest server/tests/unit/test_config.py -q)
  (cd "$PROJECT_ROOT/client" && npm run type-check)

  if command -v podman >/dev/null 2>&1; then
    podman ps >/dev/null 2>&1 || log_warn "Podman instalado, mas a verificação 'podman ps' falhou"
  fi

  if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
    log_info "Docker acessível pelo usuário atual"
    if [[ $VALIDATE_COMPOSE -eq 1 ]]; then
      docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" config >/dev/null
      docker compose -f "$PROJECT_ROOT/docker-compose.monitoring.yml" config >/dev/null
      docker compose -f "$PROJECT_ROOT/docker-compose.optimized.yml" config >/dev/null
      docker compose -f "$PROJECT_ROOT/docker-compose.yml" -f "$PROJECT_ROOT/docker-compose.otel.yml" config >/dev/null
      log_info "docker compose config validado para os principais stacks"
    fi
  elif command -v docker >/dev/null 2>&1; then
    log_warn "Docker instalado, mas o usuário atual ainda não tem acesso ao daemon"
    if [[ $VALIDATE_COMPOSE -eq 1 ]]; then
      log_warn "Validação de docker compose ignorada por falta de acesso ao daemon"
    fi
  fi

  log_info "Validações básicas concluídas"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-system)
      INSTALL_SYSTEM=0
      ;;
    --with-optional)
      INSTALL_OPTIONAL=1
      ;;
    --skip-playwright)
      SKIP_PLAYWRIGHT=1
      ;;
    --refresh-env)
      REFRESH_ENV=1
      ;;
    --validate-compose)
      VALIDATE_COMPOSE=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_error "Opção desconhecida: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ClimateAI Bootstrap Environment${NC}"
echo -e "${BLUE}========================================${NC}"

cd "$PROJECT_ROOT"

if [[ $INSTALL_SYSTEM -eq 1 ]]; then
  install_system_packages
fi

prepare_env_file
setup_python
setup_node
run_validations

echo -e "${GREEN}Bootstrap concluído.${NC}"
echo "Próximos passos:"
echo "  1. Se o Docker ainda negar acesso, execute: newgrp docker"
echo "  2. Para rodar localmente: ./start-servers.sh"
echo "  3. Para validar compose: docker compose -f docker-compose.dev.yml config"