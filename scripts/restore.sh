#!/bin/bash

# ============================================
# Script de Restore de Backup do ClimateAI
# ============================================
# Restaura um backup específico do PostgreSQL
# ============================================

set -e

# Configurações
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-climateai}"
DB_USER="${DB_USER:-postgres}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Show usage
if [ $# -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 ClimateAI - Restore de Backup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Uso: $0 <arquivo_backup.sql.gz>"
    echo ""
    echo "Backups disponíveis:"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        ls -lht "$BACKUP_DIR"/climateai_*.sql.gz 2>/dev/null | head -10 || echo "  Nenhum backup encontrado"
    else
        echo "  Diretório de backups não existe: $BACKUP_DIR"
    fi
    
    echo ""
    echo "Exemplo:"
    echo "  $0 ./backups/climateai_20250120_020000.sql.gz"
    echo ""
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Arquivo de backup não encontrado: $BACKUP_FILE"
    exit 1
fi

# Verify backup integrity
log_step "Verificando integridade do backup..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    log_info "Backup íntegro"
else
    log_error "Backup corrompido!"
    exit 1
fi

# Verify checksum if available
if [ -f "${BACKUP_FILE}.sha256" ]; then
    log_step "Verificando checksum SHA256..."
    if sha256sum -c "${BACKUP_FILE}.sha256" > /dev/null 2>&1; then
        log_info "Checksum verificado com sucesso"
    else
        log_error "Checksum falhou! O backup pode estar corrompido."
        exit 1
    fi
fi

# Confirm restore
echo ""
log_warn "ATENÇÃO: Este procedimento irá sobrescrever o banco de dados atual!"
echo ""
echo "Backup: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""
read -p "Deseja continuar? (digite 'SIM' para confirmar) " -r
echo ""

if [[ ! $REPLY =~ ^SIM$ ]]; then
    log_warn "Restore cancelado"
    exit 0
fi

# Get database password
if [ -n "$DB_PASSWORD" ]; then
    export PGPASSWORD="$DB_PASSWORD"
elif [ -f ".env" ]; then
    DB_PASSWORD_ENV=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    if [ -n "$DB_PASSWORD_ENV" ]; then
        export PGPASSWORD="$DB_PASSWORD_ENV"
    fi
fi

# Step 1: Drop existing database
log_step "1️⃣  Removendo banco de dados existente..."
if dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" 2>/dev/null; then
    log_info "Banco de dados removido"
else
    log_warn "Não foi possível remover o banco de dados (pode não existir)"
fi

# Step 2: Create new database
log_step "2️⃣  Criando novo banco de dados..."
if createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"; then
    log_info "Banco de dados criado"
else
    log_error "Falha ao criar banco de dados"
    exit 1
fi

# Step 3: Restore backup
log_step "3️⃣  Restaurando backup..."
if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
    log_info "Backup restaurado com sucesso"
else
    log_error "Falha ao restaurar backup"
    exit 1
fi

# Step 4: Verify restore
log_step "4️⃣  Verificando restore..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

if [ "$TABLE_COUNT" -gt 0 ]; then
    log_info "Restore verificado: $TABLE_COUNT tabelas encontradas"
else
    log_warn "Nenhuma tabela encontrada (backup pode estar vazio)"
fi

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "Restore concluído com sucesso!"
echo ""
echo "📊 Resumo:"
echo "   Backup: $(basename $BACKUP_FILE)"
echo "   Database: $DB_NAME"
echo "   Tabelas: $TABLE_COUNT"
echo ""
echo "📋 Próximos passos:"
echo "   1. Verifique se a aplicação está funcionando"
echo "   2. Execute testes de integração"
echo "   3. Monitore logs de erro"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
