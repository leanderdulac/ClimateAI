# 🚀 ClimateAI - Deploy no DigitalOcean

Este guia mostra como fazer deploy completo da plataforma ClimateAI no DigitalOcean.

## 📋 Pré-requisitos

- Conta no [DigitalOcean](https://digitalocean.com)
- Domínio registrado (opcional, mas recomendado)
- Conhecimento básico de Linux/Docker

## 🏗️ Passo 1: Criar Droplet

### Configuração Recomendada:

1. **Acesse** [DigitalOcean Dashboard](https://cloud.digitalocean.com/)
2. **Clique** "Create" → "Droplets"
3. **Escolha**:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($12/mês - 1GB RAM, 1 vCPU) para desenvolvimento
   - **Plan**: Basic ($24/mês - 2GB RAM, 2 vCPU) para produção inicial
   - **Datacenter**: São Paulo (SP) - menor latência para usuários brasileiros
4. **Adicione** SSH Key (recomendado)
5. **Nomeie** como `climateai-prod`
6. **Create Droplet**

## 🔐 Passo 2: Acesso Inicial

```bash
# Conecte via SSH
ssh root@YOUR_DROPLET_IP

# OU se configurou SSH key
ssh -i ~/.ssh/your_key root@YOUR_DROPLET_IP
```

## 🚀 Passo 3: Executar Deploy Automático

### Opção 1: Deploy Automático (Recomendado)

```bash
# Baixe o script de deploy
wget https://raw.githubusercontent.com/leanderdulac/ClimateAI/main/deploy/deploy_digitalocean.sh
chmod +x deploy_digitalocean.sh

# Configure variáveis de ambiente
export DOMAIN="seu-dominio.com"
export EMAIL="seu-email@dominio.com"
export DB_PASSWORD="sua_senha_forte_aqui"

# Execute o deploy
./deploy_digitalocean.sh
```

### Opção 2: Deploy Manual

```bash
# Atualize o sistema
sudo apt update && sudo apt upgrade -y

# Instale Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Reinicie sessão para aplicar grupo docker
# exit e reconnect

# Clone o repositório
git clone https://github.com/leanderdulac/ClimateAI.git
cd ClimateAI

# Configure ambiente
cp .env.example .env
nano .env  # Configure suas variáveis

# Inicie a aplicação
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🌐 Passo 4: Configurar Domínio (Opcional)

### No DigitalOcean:

1. **Acesse** Networking → Domains
2. **Adicione** seu domínio
3. **Configure** os registros:
   - **A Record**: `@` → `YOUR_DROPLET_IP`
   - **CNAME**: `www` → `@`

### No Servidor:

```bash
# Configure Nginx para o domínio
sudo nano /etc/nginx/sites-available/climateai

# Adicione:
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Habilite o site
sudo ln -sf /etc/nginx/sites-available/climateai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Configure SSL
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## 📊 Passo 5: Verificar Deploy

```bash
# Verifique status dos serviços
docker-compose -f docker-compose.prod.yml ps

# Verifique logs
docker-compose -f docker-compose.prod.yml logs -f

# Teste conectividade
curl http://localhost:8000/api/v1/health
curl http://localhost:80
```

## 📈 Passo 6: Configurar Monitoramento

```bash
# Acesse Grafana
# URL: http://YOUR_DROPLET_IP:3001
# Usuário: admin
# Senha: admin

# Acesse Prometheus
# URL: http://YOUR_DROPLET_IP:9090
```

## 🔄 Passo 7: Backup Automático

O script de deploy já configura backup automático diário. Para backup manual:

```bash
# Execute backup
/opt/backup/backup.sh

# Liste backups
ls -la /opt/backup/
```

## 🛠️ Comandos Úteis

```bash
# Ver status
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f [service_name]

# Reiniciar serviço
docker-compose -f docker-compose.prod.yml restart [service_name]

# Atualizar aplicação
cd /opt/climateai
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build

# Backup manual
/opt/backup/backup.sh

# Verificar disco
df -h

# Verificar memória
free -h
```

## 🚨 Troubleshooting

### Serviço não inicia:
```bash
# Verifique logs detalhados
docker-compose -f docker-compose.prod.yml logs

# Verifique portas
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000
```

### Problemas de memória:
```bash
# Verifique uso de memória
docker stats

# Limpe containers não utilizados
docker system prune -a
```

### SSL não funciona:
```bash
# Renove certificado
sudo certbot renew

# Recarregue Nginx
sudo systemctl reload nginx
```

## 💰 Custos Estimados

| Serviço | Custo Mensal |
|---------|-------------|
| **Droplet (2GB)** | $24 |
| **Backup** | $2 |
| **Domínio** | R$ 30-50 |
| **SSL (Let's Encrypt)** | Gratuito |
| **Total** | **~R$ 200/mês** |

## 🔒 Segurança

- ✅ Firewall UFW configurado
- ✅ SSH key authentication
- ✅ SSL/TLS habilitado
- ✅ Senhas fortes definidas
- ✅ Backup automático
- ✅ Monitoramento ativo

## 📞 Suporte

Para problemas específicos:
1. Verifique os logs da aplicação
2. Consulte a documentação do Docker
3. Verifique status dos serviços
4. Contacte suporte DigitalOcean se necessário

---

## 🎯 Próximos Passos

1. **Teste** thoroughly a aplicação
2. **Configure** monitoring alerts
3. **Implemente** CDN se necessário
4. **Configure** auto-scaling quando crescer
5. **Monitore** performance e custos

**Sua ClimateAI está pronta para produção! 🚀**
