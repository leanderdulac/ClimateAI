# 💾 Etapa 7: Database Backups Automatizados

**Status:** ✅ CONCLUÍDO
**Data:** 20 de outubro de 2025
**Impacto:** Disaster recovery, compliance, business continuity

## 🎯 Objetivos Alcançados

### 1. **Backup Automático PostgreSQL** ✅
```bash
# Backup completo com pg_dump
backup.py backup

# Backup verificado e comprimido
# Opções:
# - Compressão gzip (padrão, 6 níveis)
# - Verificação automática de integridade
# - Checksum SHA256
```

### 2. **Restauração de Backups** ✅
```bash
# Restaurar de um backup
backup.py restore backup_20251020_020000.sql.gz --database climatewise_restored

# Suporta:
# - Descompressão automática
# - Verificação de integridade
# - Restauração em novo banco de dados
```

### 3. **Retenção Automática** ✅
```python
# Configuração
RETENTION_DAYS = 30          # Manter últimos 30 dias
RETENTION_COUNT = 10         # Manter no máximo 10 backups

# Limpeza automática de backups antigos
storage.cleanup_old_backups()
```

### 4. **Upload em Cloud Storage** ✅
```python
# Suporte para múltiplos destinos:
- Local (/var/backups/fimce)
- Amazon S3
- Google Cloud Storage
- Azure Blob Storage (preparado)
```

### 5. **Agendamento com Cron/Systemd** ✅
```bash
# Cron jobs configurados:
0 2 * * *     # Full backup diário às 2:00 AM
0 5 * * 0,3   # Backup extra (dom/qua)
0 3 * * 2     # Limpeza (terça)
0 1 * * *     # Verificação de disco (1:00 AM)

# Systemd timers como alternativa:
systemctl enable fimce-backup.timer
```

### 6. **Monitoramento e Notificações** ✅
```bash
# Check status dos backups
check-backups

# Notificações suportadas:
- Slack webhooks
- Email (preparado)
- Logs estruturados
```

## 📁 Arquivos Criados/Modificados

### Novos Arquivos:
1. **`server/backup.py`** (600+ linhas)
   - `BackupConfig`: Configuração centralizada
   - `DatabaseBackup`: Operações de backup/restore
   - `BackupStorage`: Gerenciamento de storage (S3, GCS, local)
   - `BackupNotification`: Envio de notificações
   - `BackupOrchestrator`: Orquestração completa

2. **`server/setup_backups.sh`** (200+ linhas)
   - Configuração automática de cron/systemd
   - Criação de diretórios
   - Setup de variáveis de ambiente
   - Instalação de scripts helpers

## 🚀 Como Usar

### 1. Setup Inicial

```bash
# Como root ou com sudo
sudo bash /home/artha/climateAI/server/setup_backups.sh

# Isso vai:
# - Criar diretórios em /var/backups/fimce
# - Configurar cron jobs
# - Criar systemd timers
# - Instalar scripts helpers
```

### 2. Configuração de Variáveis

```bash
# Em /etc/environment.d/fimce-backup:
export BACKUP_DIR=/var/backups/fimce
export BACKUP_RETENTION_DAYS=30
export BACKUP_RETENTION_COUNT=10
export BACKUP_COMPRESS=true
export BACKUP_VERIFY=true

# Database (obrigatório)
export DATABASE_URL=postgresql://user:pass@host:5432/climatewise

# S3 (opcional)
export BACKUP_S3_BUCKET=climatewise-backups
export AWS_REGION=us-east-1

# GCS (opcional)
export BACKUP_GCS_BUCKET=climatewise-backups-gcs
export GCP_PROJECT_ID=my-project-id

# Notificações (opcional)
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export BACKUP_EMAIL_TO=ops@climatewise.com
```

### 3. Testando

```bash
# Executar backup manualmente
test-backup

# Listar backups existentes
/usr/bin/python3 /home/artha/climateAI/server/backup.py list

# Verificar status
check-backups
```

### 4. Restauração de Emergência

```bash
# Listar backups disponíveis
backup.py list

# Restaurar em novo banco de dados
backup.py restore /var/backups/fimce/backup_20251020_020000.sql.gz \
  --database climatewise_backup_restored

# Depois, migrar dados conforme necessário
```

## 📊 Estrutura de Backup

```
/var/backups/fimce/
├── logs/
│   ├── 20251020_020000.log
│   ├── backup.log (log atual)
│   ├── cleanup.log
│   └── disk-usage.log
├── restore/
│   └── (arquivos temporários de restore)
├── backup_20251020_020000.sql.gz
├── backup_20251019_020000.sql.gz
├── backup_20251018_020000.sql.gz
└── ...
```

## 🔄 Fluxo de Backup

```
1. Schedule (cron/systemd)
   ↓
2. DatabaseBackup.create_backup()
   - Parse DATABASE_URL
   - Execute pg_dump
   - Compactar (gzip)
   ↓
3. DatabaseBackup.verify_backup()
   - Validar arquivo gzip
   - Calcular checksum SHA256
   ↓
4. BackupStorage.upload_to_s3()
   - Upload para bucket S3
   ↓
5. BackupStorage.upload_to_gcs()
   - Upload para GCS (se configurado)
   ↓
6. BackupStorage.cleanup_old_backups()
   - Remover backups > 30 dias
   - Manter máximo 10 backups
   ↓
7. BackupNotification.send_slack()
   - Notificar sucesso/falha
   ↓
✅ Concluído
```

## 📈 Métricas de Backup

### Tamanho Típico
```
Database original: 500 MB
Após pg_dump:      500 MB (SQL text)
Após gzip:         50 MB (90% compressão)
Tempo:             ~5-15 minutos
```

### Retenção
```
30 dias com 1 backup/dia:
- 30 backups × 50 MB = 1.5 GB (com retenção_count=10: 500 MB)

1 ano com 1 backup/semana:
- 52 backups × 50 MB = 2.6 GB
```

## 🔐 Segurança

### Permissões
```bash
# Diretório de backup: somente leitura para www-data
chmod 700 /var/backups/fimce
chown www-data:www-data /var/backups/fimce

# Arquivo de backup: proprietário only
chmod 600 /var/backups/fimce/backup_*.sql.gz
```

### Credenciais
```bash
# Não armazenar password em texto plano
# Usar .pgpass:
echo "localhost:5432:climatewise:user:password" > ~/.pgpass
chmod 600 ~/.pgpass

# OU usar PGPASSWORD via environment (menos seguro)
export PGPASSWORD="sua_senha_aqui"
```

### Encryption
```bash
# Criptografar backup com GPG (antes de enviar para cloud)
gpg --symmetric --cipher-algo AES256 backup_20251020_020000.sql.gz

# Descriptografar
gpg --decrypt backup_20251020_020000.sql.gz.gpg > backup_20251020_020000.sql.gz
```

## 🚨 Troubleshooting

### Problema: "pg_dump command not found"
```bash
# Instalar PostgreSQL client
apt-get install postgresql-client
# ou
yum install postgresql
```

### Problema: "Permission denied" ao escrever em /var/backups
```bash
# Verificar permissões
ls -la /var/backups/fimce

# Corrigir ownership
sudo chown www-data:www-data /var/backups/fimce
sudo chmod 700 /var/backups/fimce
```

### Problema: Backup não inicia via cron
```bash
# Verificar cron logs
grep CRON /var/log/syslog

# Verificar se arquivo existe
ls -la /etc/cron.d/fimce-backup

# Testar manualmente
sudo -u www-data /usr/bin/python3 /home/artha/climateAI/server/backup.py backup
```

### Problema: Espaço em disco insuficiente
```bash
# Verificar uso
du -sh /var/backups/fimce

# Aumentar retenção para menos dias
export BACKUP_RETENTION_DAYS=15

# Ou aumentar armazenamento
# Remover backups antigos manualmente
rm /var/backups/fimce/backup_*.sql.gz -t +60  # Remove tudo > 60 dias
```

## 📋 Checklist de Validação

- ✅ `server/backup.py` criado com todas as classes
- ✅ `server/setup_backups.sh` cria cron/systemd
- ✅ Backup pode ser criado e comprimido
- ✅ Restauração funciona em novo banco
- ✅ Verificação de integridade funciona
- ✅ Limpeza automática de backups antigos
- ✅ Upload para S3 (se configurado)
- ✅ Upload para GCS (se configurado)
- ✅ Notificações via Slack
- ✅ Scripts helpers (check-backups, test-backup)

## 📊 Exemplo de Dashboard Monitoramento

```bash
$ check-backups

📊 Status de Backups FIMCE
================================

📁 Diretório: /var/backups/fimce

📋 Total de backups: 8

📅 Últimos backups:
  backup_20251020_020000.sql.gz (52 MB)
  backup_20251019_020000.sql.gz (51 MB)
  backup_20251018_020000.sql.gz (50 MB)
  backup_20251017_020000.sql.gz (50 MB)
  backup_20251016_020000.sql.gz (51 MB)

💾 Uso de disco:
  Total: 408 MB
  Disponível: 250 GB / 500 GB

✅ Último backup: 2025-10-20 02:00:15 (52 MB)

📝 Últimos erros nos logs:
  ✓ Nenhum erro encontrado
```

## 🔄 Próxima Etapa

**Etapa 8: Complete Test Coverage** (Cobertura de Testes)
- Unit tests para todos os módulos
- Integration tests com database real
- Coverage reporting (>80%)
- CI/CD pipeline validation

---

**Tempo Total de Implementação:** ~2.5 horas
**Complexidade:** ⭐⭐⭐ (Média)
**Manutenibilidade:** ⭐⭐⭐⭐ (Boa)
