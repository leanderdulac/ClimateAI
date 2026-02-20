# 🗄️ Banco de Dados - ClimateAI

## ✅ Status: CONFIGURADO

Banco de dados inicializado com tabelas e usuários de teste.

---

## 📊 Estrutura do Banco

### Tabelas Criadas

| Tabela | Descrição |
|--------|-----------|
| `users` | Usuários do sistema |
| `policies` | Apólices/seguros |
| `climate_events` | Eventos climáticos |
| `claims` | Sinistros |
| `audit_logs` | Logs de auditoria |

### Extensões
- `uuid-ossp` - Geração de UUIDs

---

## 👥 Usuários de Teste

| Email | Senha | Role |
|-------|-------|------|
| `admin@climateai.com` | `admin123` | Admin |
| `user@climateai.com` | `user123` | User |

### ⚠️ Importante
As senhas acima são **apenas para desenvolvimento**. Em produção, use hashes bcrypt seguros.

---

## 🔧 Comandos Úteis

### Verificar Status do Banco
```bash
./scripts/check-db.sh
```

### Acessar PostgreSQL
```bash
# Shell interativo
podman exec -it climateai-db psql -U postgres -d climateai

# Executar comando
podman exec -it climateai-db psql -U postgres -d climateai -c "SELECT * FROM users;"
```

### Listar Tabelas
```bash
podman exec climateai-db psql -U postgres -d climateai -c "\dt"
```

### Resetar Banco (CUIDADO: apaga dados!)
```bash
podman exec -i climateai-db psql -U postgres -d climateai < server/init-db.sql
```

### Backup
```bash
podman exec climateai-db pg_dump -U postgres -d climateai > backup_$(date +%Y%m%d).sql
```

### Restore
```bash
podman exec -i climateai-db psql -U postgres -d climateai < backup_20260217.sql
```

---

## 📝 Configuração de Conexão

### Docker Compose
```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: climateai123
      POSTGRES_DB: climateai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Application (.env)
```bash
DATABASE_URL=postgresql+asyncpg://postgres:climateai123@localhost:5432/climateai
DB_USER=postgres
DB_PASSWORD=climateai123
DB_NAME=climateai
DB_HOST=localhost
DB_PORT=5432
```

---

## 🔍 Queries Úteis

### Ver Usuários
```sql
SELECT id, email, full_name, role, created_at 
FROM users 
ORDER BY created_at DESC;
```

### Ver Políticas
```sql
SELECT p.*, u.email 
FROM policies p 
JOIN users u ON p.user_id = u.id 
ORDER BY p.created_at DESC;
```

### Ver Sinistros
```sql
SELECT c.*, p.policy_number, e.event_type 
FROM claims c 
JOIN policies p ON c.policy_id = p.id 
LEFT JOIN climate_events e ON c.event_id = e.id 
ORDER BY c.filed_at DESC;
```

### Logs de Auditoria
```sql
SELECT a.*, u.email 
FROM audit_logs a 
LEFT JOIN users u ON a.user_id = u.id 
ORDER BY a.created_at DESC 
LIMIT 100;
```

---

## 🚨 Troubleshooting

### Erro: "usuário não encontrado"

**Causa:** Tabela users vazia ou usuário não criado.

**Solução:**
```bash
# Recriar tabelas e usuários
podman exec -i climateai-db psql -U postgres -d climateai < server/init-db.sql
```

### Erro: "banco de dados não existe"

**Causa:** Banco climateai não foi criado.

**Solução:**
```bash
# Criar banco
podman exec -it climateai-db psql -U postgres -c "CREATE DATABASE climateai;"

# Ou recriar container
podman rm -f climateai-db
podman run -d --name climateai-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=climateai123 \
  -e POSTGRES_DB=climateai \
  -p 5432:5432 \
  postgres:16-alpine
```

### Erro: "senha incorreta"

**Causa:** Senha do .env não corresponde à do container.

**Solução:**
```bash
# Verificar senha no docker-compose.yml ou comando de inicialização
# Atualizar .env com a senha correta
```

---

## 📚 Scripts Disponíveis

| Script | Descrição |
|--------|-----------|
| `scripts/check-db.sh` | Verifica status do banco |
| `server/init-db.sql` | Script de inicialização |

---

*Documento criado em: 17 de Fevereiro de 2026*  
*Status: ✅ CONFIGURADO E OPERACIONAL*
