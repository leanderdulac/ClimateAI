# 🚀 Guia de Deploy em Produção - ClimateWise

## Status: ✅ PRONTO PARA PRODUÇÃO

---

## 📋 Pré-requisitos

### Servidor
- **OS**: Ubuntu 22.04 LTS ou superior
- **CPU**: 4 cores (mínimo 2)
- **RAM**: 8 GB (mínimo 4 GB)
- **Storage**: 50 GB SSD
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Domínio e SSL
- Domínio configurado (ex: climatewise.com)
- Certificado SSL (Let's Encrypt recomendado)

---

## 🔧 1. Configuração do Servidor

### 1.1. Instalar Dependências

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Git
sudo apt install -y git

# Instalar Nginx
sudo apt install -y nginx

# Reiniciar sessão
newgrp docker
```

### 1.2. Clonar Repositório

```bash
cd /var/www
sudo git clone https://github.com/leanderdulac/ClimateWise.git
sudo chown -R $USER:$USER ClimateWise
cd ClimateWise
```

---

## 🔐 2. Configuração de Segurança

### 2.1. Gerar SECRET_KEY

```bash
# Gerar chave segura
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copiar resultado
```

### 2.2. Configurar .env

```bash
# Copiar template
cp .env.example .env

# Editar .env
nano .env
```

**Variáveis CRÍTICAS para produção**:

```ini
# Segurança
SECRET_KEY=<sua_chave_gerada_acima>
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/climatewise
DB_PASSWORD=<senha_forte>
POSTGRES_PASSWORD=<senha_forte>

# CORS (SEU DOMÍNIO REAL)
ALLOW_ORIGINS=https://climatewise.com,https://www.climatewise.com

# APIs Externas
EMBRAPA_API_KEY=sua_chave
NOAA_API_KEY=sua_chave
GEMINI_API_KEY=sua_chave

# Unified Pricing NOAA (ajuste operacional)
# Peso NOAA no combined_risk_score (0.0 a 1.0)
NOAA_RISK_BLEND_WEIGHT=0.15
# Impacto máximo NOAA no prêmio (0.0 a 0.5)
NOAA_PREMIUM_MAX_IMPACT=0.12

# Domínio
DOMAIN=climatewise.com
```

**Notas operacionais (Unified Pricing + NOAA):**
- Em operação conservadora inicial, mantenha `NOAA_RISK_BLEND_WEIGHT=0.15` e `NOAA_PREMIUM_MAX_IMPACT=0.12`.
- Se NOAA estiver indisponível, o orquestrador aplica fallback neutro (sem ajuste de risco e sem aumento de prêmio por NOAA).
- Para rollout gradual, aumente os valores em passos pequenos (ex.: `0.15 -> 0.20`) e acompanhe métricas de sinistralidade e variação de prêmio.

### 2.3. Configurar Firewall

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow 22

# Permitir HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Bloquear portas internas (apenas Docker)
sudo ufw deny 5432
sudo ufw deny 6379
sudo ufw deny 8000

# Verificar status
sudo ufw status
```

---

## 🐳 3. Deploy com Docker

### 3.1. Build das Imagens

```bash
# Build para produção
docker compose -f docker-compose.prod.yml build

# Verificar imagens
docker images
```

### 3.2. Iniciar Serviços

```bash
# Iniciar todos os serviços
docker compose -f docker-compose.prod.yml up -d

# Verificar status
docker compose ps

# Verificar logs
docker compose logs -f
```

### 3.3. Configurar Database

```bash
# Aguardar PostgreSQL estar pronto
sleep 10

# Rodar migrações
docker compose exec backend alembic upgrade head

# Criar dados iniciais (seed)
docker compose exec backend python seed_db.py
```

---

## 🌐 4. Configurar Nginx (Reverse Proxy)

### 4.1. Criar Configuração do Nginx

```bash
sudo nano /etc/nginx/sites-available/climatewise
```

**Configuração**:

```nginx
server {
    listen 80;
    server_name climatewise.com www.climatewise.com;
    
    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name climatewise.com www.climatewise.com;
    
    # SSL (preencher após criar certificado)
    ssl_certificate /etc/letsencrypt/live/climatewise.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/climatewise.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Landing Page
    location /landing {
        alias /var/www/ClimateWise/landing-page.html;
        index landing-page.html;
    }
    
    # Static files
    location /static {
        alias /var/www/ClimateWise/server/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4.2. Habilitar Site

```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/climatewise /etc/nginx/sites-enabled/

# Testar configuração
sudo nginx -t

# Recarregar Nginx
sudo systemctl reload nginx
```

---

## 🔒 5. Configurar SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d climatewise.com -d www.climatewise.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

---

## 📊 6. Configurar Monitoramento

### 6.1. Iniciar Stack de Monitoramento

```bash
# Iniciar Prometheus, Grafana, etc.
docker compose -f docker-compose.monitoring.yml up -d
```

### 6.2. Acessar Dashboards

- **Grafana**: http://climatewise.com:3001 (admin/admin)
- **Prometheus**: http://climatewise.com:9090
- **Kibana**: http://climatewise.com:5601

### 6.3. Configurar Alertas

```bash
# Editar alertas do Prometheus
nano monitoring/prometheus/alerts.yml
```

---

## 💾 7. Configurar Backups Automáticos

### 7.1. Configurar Script de Backup

```bash
# Tornar executável
chmod +x scripts/backup.sh

# Testar backup
./scripts/backup.sh
```

### 7.2. Configurar Cron

```bash
# Editar crontab
crontab -e

# Adicionar backup diário às 2 AM
0 2 * * * cd /var/www/ClimateWise && ./scripts/backup.sh >> ./logs/backup_cron.log 2>&1
```

### 7.3. Configurar Upload para S3 (Opcional)

```bash
# Instalar AWS CLI
sudo apt install -y awscli

# Configurar credenciais
aws configure

# Editar .env
nano .env

# Adicionar:
BACKUP_S3_BUCKET=meu-bucket-backup
AWS_REGION=us-east-1
```

---

## 🧪 8. Verificação Final

### 8.1. Rodar Script de Verificação

```bash
./scripts/verify_platform.sh
```

### 8.2. Testar Endpoints

```bash
# Health check
curl https://climatewise.com/health

# API docs
curl https://climatewise.com/docs

# Testar login
curl -X POST https://climatewise.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@climatewise.com","password":"senha"}'
```

### 8.3. Verificar Logs

```bash
# Backend
docker compose logs -f backend

# Frontend
docker compose logs -f frontend

# Database
docker compose logs -f db
```

---

## 🔄 9. Deploy Contínuo (CI/CD)

### 9.1. GitHub Actions

O projeto já inclui workflows em `.github/workflows/`:

- `ci.yml`: Testes e linting
- `cd.yml`: Deploy automático
- `security.yml`: Varredura de segurança

### 9.2. Deploy Automático

```bash
# Configurar webhook no GitHub
# Settings > Webhooks > Add webhook
# Payload URL: https://climatewise.com/hooks/deploy
# Secret: <webhook_secret>
# Events: Push
```

---

## 🚨 10. Procedimentos de Emergência

### 10.1. Rollback de Deploy

```bash
# Parar serviços
docker compose down

# Reverter para versão anterior
git checkout <tag-anterior>

# Rebuild e restart
docker compose -f docker-compose.prod.yml up -d --build
```

### 10.2. Restore de Database

```bash
# Listar backups
ls -lh backups/

# Restaurar
./scripts/restore.sh backups/climatewise_YYYYMMDD_HHMMSS.sql.gz
```

### 10.3. Emergency Contacts

```
- Tech Lead: [nome]@[dominio].com
- DevOps: [nome]@[dominio].com
- On-call: +XX XXXX-XXXX
```

---

## 📈 11. Otimizações de Produção

### 11.1. Database

```sql
-- Criar índices
CREATE INDEX idx_clima_data ON clima_data(data);
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- Analisar tabelas
ANALYZE;
```

### 11.2. Cache Redis

```bash
# Configurar maxmemory
docker compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 11.3. Connection Pooling

```python
# Configurar em config/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)
```

---

## ✅ Checklist Final de Deploy

- [ ] SECRET_KEY configurada e segura
- [ ] DEBUG=False
- [ ] CORS configurado com domínios reais
- [ ] Database com senha forte
- [ ] SSL/HTTPS configurado
- [ ] Firewall habilitado
- [ ] Backups automáticos rodando
- [ ] Monitoramento ativo
- [ ] Logs centralizados
- [ ] Health checks passando
- [ ] Tests passando
- [ ] Documentação atualizada

---

## 📚 Recursos Adicionais

- **Documentação da API**: https://climatewise.com/docs
- **Status Page**: https://status.climatewise.com
- **Runbook**: /docs/RUNBOOK.md
- **Playbooks**: /docs/playbooks/

---

## 🎯 Próximos Passos

1. **Semana 1**: Monitorar métricas de performance
2. **Semana 2**: Otimizar queries lentas
3. **Semana 3**: Implementar caching avançado
4. **Semana 4**: Revisar segurança (pentest)

---

**Última atualização**: Fevereiro 2026  
**Versão**: 1.0.0  
**Status**: ✅ Produção
