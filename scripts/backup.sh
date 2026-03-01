#!/bin/bash

# ============================================
# Script de Backup Automático do ClimateWise
# ============================================
# Backup de PostgreSQL com compressão,
# verificação de integridade e retenção automática
# ============================================

set -e

# Configurações
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-climatewise}"
DB_USER="${DB_USER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-9}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/climatewise_${TIMESTAMP}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Functions
log_info() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${BLUE}▶${NC} $1" | tee -a "$LOG_FILE"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 ClimateWise - Backup Automático"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log_step "Iniciando backup em $(date)"
echo ""

# Step 1: Check PostgreSQL connection
log_step "1️⃣  Verificando conexão com PostgreSQL..."
if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    log_info "PostgreSQL acessível"
else
    log_error "Não foi possível conectar ao PostgreSQL"
    log_error "Host: $DB_HOST:$DB_PORT, User: $DB_USER"
    exit 1
fi

# Step 2: Create backup
log_step "2️⃣  Criando backup do banco de dados..."
log_info "Database: $DB_NAME"

# Get database password from environment or .env file
if [ -n "$DB_PASSWORD" ]; then
    export PGPASSWORD="$DB_PASSWORD"
elif [ -f ".env" ]; then
    DB_PASSWORD_ENV=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    if [ -n "$DB_PASSWORD_ENV" ]; then
        export PGPASSWORD="$DB_PASSWORD_ENV"
    fi
fi

# Create backup with pg_dump
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --verbose 2>&1 | gzip -${COMPRESSION_LEVEL} > "$BACKUP_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup criado: $BACKUP_FILE"
    log_info "Tamanho: $BACKUP_SIZE"
else
    log_error "Falha ao criar backup"
    exit 1
fi

# Step 3: Verify backup integrity
log_step "3️⃣  Verificando integridade do backup..."
if gzip -t "$BACKUP_FILE" 2>/dev/null; then
    log_info "Backup íntegro (verificação gzip OK)"
    
    # Calculate checksum
    CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
    echo "$CHECKSUM  $BACKUP_FILE" > "${BACKUP_FILE}.sha256"
    log_info "Checksum SHA256: ${CHECKSUM:0:16}..."
else
    log_error "Backup corrompido!"
    exit 1
fi

# Step 4: Test restore (optional, can be slow)
if [ "${TEST_RESTORE:-false}" = "true" ]; then
    log_step "4️⃣  Testando restore (opcional)..."
    TEST_DB="${DB_NAME}_test_restore_${TIMESTAMP}"
    
    # Create test database
    createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEST_DB" > /dev/null 2>&1
    
    # Restore
    if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$TEST_DB" > /dev/null 2>&1; then
        log_info "Teste de restore bem-sucedido"
    else
        log_warn "Teste de restore falhou (backup pode estar incompleto)"
    fi
    
    # Drop test database
    dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$TEST_DB" > /dev/null 2>&1
fi

# Step 5: Cleanup old backups
log_step "5️⃣  Limpando backups antigos (retenção: $RETENTION_DAYS dias)..."
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "climatewise_*.sql.gz" -type f -mtime +$RETENTION_DAYS | wc -l)

if [ "$OLD_BACKUPS" -gt 0 ]; then
    find "$BACKUP_DIR" -name "climatewise_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "climatewise_*.sha256" -type f -mtime +$RETENTION_DAYS -delete
    log_info "$OLD_BACKUPS backups antigos removidos"
else
    log_info "Nenhum backup antigo para remover"
fi

# Step 6: Upload to cloud storage (optional)
if [ -n "$BACKUP_S3_BUCKET" ]; then
    log_step "6️⃣  Upload para S3..."
    if command -v aws &> /dev/null; then
        aws s3 cp "$BACKUP_FILE" "s3://${BACKUP_S3_BUCKET}/climatewise/$(basename $BACKUP_FILE)"
        log_info "Backup enviado para S3"
    else
        log_warn "AWS CLI não instalado, skipando upload S3"
    fi
fi

if [ -n "$BACKUP_GCS_BUCKET" ]; then
    log_step "6️⃣  Upload para Google Cloud Storage..."
    if command -v gsutil &> /dev/null; then
        gsutil cp "$BACKUP_FILE" "gs://${BACKUP_GCS_BUCKET}/climatewise/$(basename $BACKUP_FILE)"
        log_info "Backup enviado para GCS"
    else
        log_warn "gsutil não instalado, skipando upload GCS"
    fi
fi

# Step 7: Send notification (optional)
send_notification() {
    local status=$1
    local message=$2
    
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"ClimateWise Backup: ${status}\\n${message}\"}" \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || true
    fi
    
    if [ -n "$BACKUP_EMAIL_TO" ]; then
        echo "$message" | mail -s "ClimateWise Backup: ${status}" "$BACKUP_EMAIL_TO" || true
    fi
}

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "Backup concluído com sucesso!"
echo ""
echo "📊 Resumo:"
echo "   Arquivo: $(basename $BACKUP_FILE)"
echo "   Tamanho: $BACKUP_SIZE"
echo "   Localização: $(realpath $BACKUP_DIR)"
echo "   Checksum: ${CHECKSUM:0:32}..."
echo ""
echo "📋 Comandos úteis:"
echo "   Listar backups:  ls -lh $BACKUP_DIR"
echo "   Restaurar:       gunzip -c $BACKUP_FILE | psql -h $DB_HOST -U $DB_USER $DB_NAME"
echo "   Verificar:       gzip -t $BACKUP_FILE"
echo ""

# Send success notification
send_notification "✅ SUCESSO" "Backup criado: $(basename $BACKUP_FILE) (${BACKUP_SIZE})"

log_info "Backup finalizado em $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
