#!/bin/bash
# Setup de Backup Automático para FIMCE
#
# Este script configura backups automáticos usando cron
# Execução: sudo bash setup_backups.sh

set -e

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🔧 Setup de Backups Automáticos${NC}"
echo -e "${BLUE}================================${NC}\n"

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Este script precisa ser executado com sudo${NC}"
    exit 1
fi

BACKUP_DIR="/var/backups/fimce"
BACKUP_USER="www-data"  # Usuário da aplicação
BACKUP_SCRIPT="/home/artha/climateAI/server/backup.py"
CRON_FILE="/etc/cron.d/fimce-backup"

# 1. Criar diretórios
echo -e "${YELLOW}Criando diretórios...${NC}"
mkdir -p "$BACKUP_DIR/logs"
mkdir -p "$BACKUP_DIR/restore"
chown -R "$BACKUP_USER:$BACKUP_USER" "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

# 2. Configurar variáveis de ambiente
echo -e "${YELLOW}Configurando variáveis de ambiente...${NC}"
cat > /etc/environment.d/fimce-backup << 'EOF'
# FIMCE Backup Configuration
BACKUP_DIR=/var/backups/fimce
BACKUP_RETENTION_DAYS=30
BACKUP_RETENTION_COUNT=10
BACKUP_COMPRESS=true
BACKUP_VERIFY=true
# DATABASE_URL configurada em /etc/default/fimce ou na aplicação
# S3
BACKUP_S3_BUCKET=climatewise-backups
AWS_REGION=us-east-1
# GCS
BACKUP_GCS_BUCKET=
GCP_PROJECT_ID=
# Azure
BACKUP_AZURE_CONTAINER=
AZURE_STORAGE_ACCOUNT=
# Slack
SLACK_WEBHOOK_URL=
BACKUP_EMAIL_TO=
EOF

# 3. Configurar cron jobs
echo -e "${YELLOW}Configurando cron jobs...${NC}"

# Diário às 2:00 AM (full backup)
cat > "$CRON_FILE" << 'EOF'
# FIMCE Database Backups
# Format: minute hour day month dayofweek user command

# Full backup diário às 2:00 AM
0 2 * * * $BACKUP_USER /usr/bin/python3 /home/artha/climateAI/server/backup.py backup >> /var/backups/fimce/logs/backup.log 2>&1

# Backup adicional em horário de baixo uso (5:00 AM)
0 5 * * 0,3 $BACKUP_USER /usr/bin/python3 /home/artha/climateAI/server/backup.py backup >> /var/backups/fimce/logs/backup.log 2>&1

# Limpeza de backups antigos (toda terça às 3:00 AM)
0 3 * * 2 root find /var/backups/fimce -name "backup_*.sql*" -mtime +30 -delete >> /var/backups/fimce/logs/cleanup.log 2>&1

# Verificação de espaço em disco (diário às 1:00 AM)
0 1 * * * root df -h /var/backups >> /var/backups/fimce/logs/disk-usage.log 2>&1
EOF

chmod 644 "$CRON_FILE"

# 4. Criar script de monitoramento
echo -e "${YELLOW}Criando script de monitoramento...${NC}"
cat > /usr/local/bin/check-backups << 'EOF'
#!/bin/bash
# Verificar status dos backups

BACKUP_DIR="/var/backups/fimce"

echo "📊 Status de Backups FIMCE"
echo "================================"
echo ""
echo "📁 Diretório: $BACKUP_DIR"
echo ""

# Contar backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_*.sql* 2>/dev/null | wc -l)
echo "📋 Total de backups: $BACKUP_COUNT"
echo ""

# Mostrar últimos 5 backups
echo "📅 Últimos backups:"
ls -lh "$BACKUP_DIR"/backup_*.sql* 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# Uso de disco
echo "💾 Uso de disco:"
du -sh "$BACKUP_DIR" | awk '{print "  Total: " $1}'
df -h "$BACKUP_DIR" | tail -1 | awk '{print "  Disponível: " $4 " / " $2}'
echo ""

# Último backup
LAST_BACKUP=$(ls -t "$BACKUP_DIR"/backup_*.sql* 2>/dev/null | head -1)
if [ ! -z "$LAST_BACKUP" ]; then
    LAST_TIME=$(date -r "$LAST_BACKUP" '+%Y-%m-%d %H:%M:%S')
    LAST_SIZE=$(ls -lh "$LAST_BACKUP" | awk '{print $5}')
    echo "✅ Último backup: $LAST_TIME ($LAST_SIZE)"
else
    echo "❌ Nenhum backup encontrado"
fi

# Verificar logs de erro
echo ""
echo "📝 Últimos erros nos logs:"
grep -i "error\|failed" "$BACKUP_DIR"/logs/*.log 2>/dev/null | tail -5 || echo "  ✓ Nenhum erro encontrado"
EOF

chmod +x /usr/local/bin/check-backups

# 5. Criar systemd timer (alternativa ao cron)
echo -e "${YELLOW}Criando systemd timer...${NC}"
cat > /etc/systemd/system/fimce-backup.service << 'EOF'
[Unit]
Description=FIMCE Database Backup
After=network.target

[Service]
Type=oneshot
User=www-data
Environment="PATH=/usr/bin:/bin"
Environment="BACKUP_DIR=/var/backups/fimce"
EnvironmentFile=/etc/environment.d/fimce-backup
ExecStart=/usr/bin/python3 /home/artha/climateAI/server/backup.py backup
StandardOutput=journal
StandardError=journal
EOF

cat > /etc/systemd/system/fimce-backup.timer << 'EOF'
[Unit]
Description=FIMCE Database Backup Timer
Requires=fimce-backup.service

[Timer]
# Executar às 2:00 AM todos os dias
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Unit=fimce-backup.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable fimce-backup.timer

# 6. Criar script de teste
echo -e "${YELLOW}Criando script de teste de backup...${NC}"
cat > /usr/local/bin/test-backup << 'EOF'
#!/bin/bash
# Testar backup manualmente

echo "🔄 Iniciando teste de backup..."
/usr/bin/python3 /home/artha/climateAI/server/backup.py backup

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backup de teste concluído com sucesso!"
else
    echo ""
    echo "❌ Backup de teste falhou!"
fi

echo ""
echo "Verifique os logs em: /var/backups/fimce/logs/"
EOF

chmod +x /usr/local/bin/test-backup

# 7. Resumo
echo -e "${GREEN}✓ Setup concluído!${NC}\n"

echo -e "${BLUE}📋 Configuração Resumida:${NC}"
echo "  Diretório de backups: $BACKUP_DIR"
echo "  Retenção: 30 dias / 10 backups"
echo "  Compressão: ativada"
echo "  Verificação: ativada"
echo ""

echo -e "${BLUE}⏰ Agendamentos (cron):${NC}"
echo "  • Full backup: Diariamente às 2:00 AM"
echo "  • Backup extra: Domingos e quartas às 5:00 AM"
echo "  • Limpeza: Terças às 3:00 AM"
echo "  • Verificação de disco: Diariamente às 1:00 AM"
echo ""

echo -e "${BLUE}🧪 Testando backup:${NC}"
/usr/local/bin/test-backup
echo ""

echo -e "${BLUE}📊 Status dos backups:${NC}"
/usr/local/bin/check-backups
echo ""

echo -e "${YELLOW}Próximas etapas:${NC}"
echo "  1. Configurar DATABASE_URL em /etc/default/fimce"
echo "  2. Configurar SLACK_WEBHOOK_URL em /etc/environment.d/fimce-backup (opcional)"
echo "  3. Configurar credenciais S3/GCS (opcional)"
echo "  4. Testar com: test-backup"
echo "  5. Monitorar com: check-backups"
echo ""

echo -e "${GREEN}✅ Sistema de backups configurado!${NC}"
