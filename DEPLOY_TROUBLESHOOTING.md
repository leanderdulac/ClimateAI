# 🔧 ClimateWise - Guia de Correção de Deploy

## 🚨 Problemas Identificados e Soluções

### **1. Erro no Netlify**

#### **Problema Comum:**
- ❌ App não carrega após deploy
- ❌ Tela branca ou erro 404
- ❌ Rotas não funcionam

#### **Soluções Implementadas:**

**A. Criado `netlify.toml`** ✅
```toml
# Configuração para SPA (Single Page Application)
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**B. Atualizado `vite.config.ts`** ✅
- Desabilitado sourcemap em produção
- Configurado outDir correto
- Adicionado emptyOutDir: true

**C. Configuração de Build**
```bash
# Build command
cd client && npm install && npm run build

# Publish directory
client/dist
```

### **2. Erro no DigitalOcean**

#### **Problemas Comuns:**
- ❌ Script de deploy falha
- ❌ Docker não inicia
- ❌ Permissões incorretas

#### **Soluções Implementadas:**

**A. Script Melhorado** ✅
- Adicionado `-euo pipefail` para melhor tratamento de erros
- Validação de pré-requisitos
- Logs mais detalhados

**B. Pré-requisitos**
```bash
# Antes de executar o deploy
1. Verificar se Docker está instalado
2. Verificar permissões do usuário
3. Configurar variáveis de ambiente
```

---

## 🚀 Deploy no Netlify (Corrigido)

### **Método 1: Via Interface Web**

1. **Conectar Repositório**
   - Acesse [Netlify](https://app.netlify.com)
   - "Import from Git" → GitHub
   - Selecione `ClimateWise`

2. **Configurar Build**
   - **Build command**: `cd client && npm install && npm run build`
   - **Publish directory**: `client/dist`
   - **Node version**: `18.0.0`

3. **Deploy**
   - Clique "Deploy site"
   - Aguarde build completar

### **Método 2: Via CLI**

```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd /home/artha/climateAI
netlify deploy --prod --dir=client/dist

# Ou deploy automático
netlify init
```

### **Configuração de Variáveis de Ambiente**

No painel do Netlify:
1. Site settings → Environment variables
2. Adicionar:
   - `NODE_VERSION` = `18.0.0`
   - `NPM_VERSION` = `8.0.0`

---

## 🐳 Deploy no DigitalOcean (Corrigido)

### **Verificação Pré-Deploy**

```bash
# 1. Verificar requisitos localmente
./test_deploy.sh

# 2. Validar Docker compose
docker compose -f docker-compose.prod.yml config --quiet

# 3. Testar build
cd client && npm run build
```

### **Deploy Passo a Passo**

#### **1. Criar Droplet**
- Ubuntu 22.04 LTS
- 2GB RAM mínimo
- São Paulo (SP)

#### **2. Conectar via SSH**
```bash
ssh root@YOUR_DROPLET_IP
```

#### **3. Instalar Dependências**
```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Adicionar usuário ao grupo docker
usermod -aG docker $USER

# Relogar para aplicar grupo
exit
# Conectar novamente
ssh root@YOUR_DROPLET_IP
```

#### **4. Clonar Repositório**
```bash
git clone https://github.com/leanderdulac/ClimateWise.git
cd ClimateWise
```

#### **5. Configurar Ambiente**
```bash
# Copiar template
cp .env.example .env

# Editar variáveis
nano .env

# Configurar:
# - DB_PASSWORD (senha forte)
# - SECRET_KEY (gerar com: openssl rand -hex 32)
# - DOMAIN (seu domínio)
```

#### **6. Executar Deploy**
```bash
# Dar permissão
chmod +x deploy/deploy_digitalocean.sh

# Configurar variáveis
export DOMAIN="seu-dominio.com"
export EMAIL="admin@dominio.com"
export DB_PASSWORD="senha_forte_aqui"

# Executar
./deploy/deploy_digitalocean.sh
```

### **Troubleshooting DigitalOcean**

#### **Erro: Docker não encontrado**
```bash
# Verificar instalação
docker --version

# Se não instalado
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

#### **Erro: Permissão negada**
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Relogar
exit
ssh root@YOUR_DROPLET_IP
```

#### **Erro: Porta em uso**
```bash
# Verificar portas
sudo netstat -tlnp | grep -E '80|443|8000|3000'

# Matar processos conflitantes
sudo killall nginx
sudo killall uvicorn
```

#### **Erro: Build falha**
```bash
# Limpar Docker
docker system prune -a -f

# Rebuild
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔍 Verificação Pós-Deploy

### **Netlify**
```bash
# Verificar site
curl https://your-app.netlify.app

# Verificar rotas
curl https://your-app.netlify.app/welcome

# Deve retornar HTML, não 404
```

### **DigitalOcean**
```bash
# Verificar serviços
docker compose -f docker-compose.prod.yml ps

# Verificar logs
docker compose -f docker-compose.prod.yml logs -f

# Testar API
curl http://localhost:8000/api/v1/health

# Testar frontend
curl http://localhost:80
```

---

## 📋 Checklist de Deploy

### **Netlify**
- [ ] Arquivo `netlify.toml` criado
- [ ] Build command configurado corretamente
- [ ] Publish directory: `client/dist`
- [ ] Node version: 18.0.0
- [ ] Redirects para SPA configurados
- [ ] Build executado com sucesso
- [ ] Site acessível na URL do Netlify

### **DigitalOcean**
- [ ] Droplet criado e acessível
- [ ] Docker instalado
- [ ] Repositório clonado
- [ ] Arquivo `.env` configurado
- [ ] Variáveis de ambiente exportadas
- [ ] Script de deploy executado
- [ ] Todos os containers rodando
- [ ] Health checks passando
- [ ] Domínio configurado (opcional)
- [ ] SSL configurado (opcional)

---

## 🆘 Logs de Erro Comuns

### **Netlify: "Failed to compile"**
```bash
# Solução: Verificar dependências
cd client
rm -rf node_modules package-lock.json
npm install
npm run build
```

### **Netlify: "404 Not Found"**
```bash
# Solução: Configurar redirects
# Arquivo netlify.toml já criado ✅
```

### **DigitalOcean: "Cannot connect to Docker daemon"**
```bash
# Solução: Reiniciar Docker
sudo systemctl restart docker
sudo systemctl enable docker
```

### **DigitalOcean: "Port already in use"**
```bash
# Solução: Parar containers conflitantes
docker compose down
docker ps -a
docker rm -f $(docker ps -aq)
```

---

## 🎯 Próximos Passos

1. **Netlify**: Executar deploy com novo `netlify.toml`
2. **DigitalOcean**: Seguir guia passo a passo acima
3. **Testar**: Validar funcionamento completo
4. **Monitorar**: Configurar alertas e logs

---

**📝 Nota**: Todos os arquivos de configuração foram corrigidos e estão prontos para uso!
