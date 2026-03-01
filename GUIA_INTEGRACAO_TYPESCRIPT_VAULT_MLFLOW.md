# 📘 Guia de Integração - TypeScript, Vault e MLflow

**Data**: 18 de Fevereiro de 2026
**Status**: ✅ **INTEGRADO NO MAIN.PY**

---

## 📊 Resumo

Todas as integrações foram adicionadas ao `server/main.py`:

| Integração | Status | Endpoints |
|------------|--------|-----------|
| **Tipos TypeScript** | ✅ OpenAPI schema | `/openapi.json` |
| **Vault Secrets** | ✅ 4 endpoints | `/api/v1/vault/*` |
| **MLflow Registry** | ✅ 4 endpoints | `/api/v1/mlflow/*` |

---

## 🔐 1. SECRETS MANAGER (HashiCorp Vault)

### Configuração

```bash
# .env
VAULT_URL=http://localhost:8200
VAULT_TOKEN=s.my-secret-token
VAULT_NAMESPACE=climatewise  # Opcional (Enterprise)
```

### Endpoints Criados

#### 1.1 Status do Vault
```http
GET /api/v1/vault/status
```

**Resposta**:
```json
{
  "enabled": true,
  "healthy": true,
  "url": "http://localhost:8200",
  "cache_ttl": 300
}
```

#### 1.2 Obter Secret
```http
GET /api/v1/vault/secrets/secret/data/climatewise/api-keys
```

**Resposta**:
```json
{
  "path": "secret/data/climatewise/api-keys",
  "keys": ["noaa_key", "gemini_key", "embrapa_key"],
  "version": "latest"
}
```

#### 1.3 Criar/Atualizar Secret
```http
POST /api/v1/vault/secrets/secret/data/climatewise/api-keys
Content-Type: application/json

{
  "noaa_key": "new-key-123",
  "gemini_key": "gemini-key-456"
}
```

**Resposta**:
```json
{
  "path": "secret/data/climatewise/api-keys",
  "status": "stored",
  "keys": ["noaa_key", "gemini_key"]
}
```

#### 1.4 Deletar Secret
```http
DELETE /api/v1/vault/secrets/secret/data/climatewise/api-keys
```

**Resposta**:
```json
{
  "path": "secret/data/climatewise/api-keys",
  "status": "deleted"
}
```

### Como Usar no Código

```python
from lib.vault_secrets import get_vault

# Obter instância singleton
vault = get_vault()

# Obter secret
api_keys = vault.get_secret("secret/data/climatewise/api-keys")
noaa_key = api_keys.get("noaa_key")

# Obter com fallback para env var
noaa_key = vault.get_secret_or_env(
    vault_path="secret/data/climatewise/api-keys",
    env_var="NOAA_API_KEY",
    key="noaa_key"
)

# Rotacionar secret
vault.rotate_secret(
    path="secret/data/climatewise/api-keys",
    key="noaa_key"
)
```

### Iniciar Vault (Dev)

```bash
# Docker
docker run -d --name vault -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=my-secret-token' \
  hashicorp/vault:latest

# Ou binário
vault server -dev -dev-root-token-id="my-secret-token"
```

### Acessar UI do Vault
```
http://localhost:8200
Token: my-secret-token
```

---

## 🤖 2. MLFLOW MODEL REGISTRY

### Configuração

```bash
# .env
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_ARTIFACT_LOCATION=file:///tmp/mlflow
```

### Endpoints Criados

#### 2.1 Status do MLflow
```http
GET /api/v1/mlflow/status
```

**Resposta**:
```json
{
  "enabled": true,
  "healthy": true,
  "tracking_uri": "http://localhost:5000",
  "registry_uri": "http://localhost:5000",
  "experiment_name": "climatewise",
  "experiment_id": "1"
}
```

#### 2.2 Listar Modelos
```http
GET /api/v1/mlflow/models
```

**Resposta**:
```json
{
  "models": [
    "climate-pricing-model",
    "risk-assessment-model",
    "precipitation-forecast"
  ],
  "count": 3
}
```

#### 2.3 Informações do Modelo
```http
GET /api/v1/mlflow/models/climate-pricing-model
```

**Resposta**:
```json
{
  "name": "climate-pricing-model",
  "description": "Modelo de precificação climática",
  "creation_timestamp": 1708272000000,
  "last_updated": 1708358400000,
  "versions": [
    {
      "version": "1",
      "stage": "Production",
      "run_id": "abc123",
      "creation_timestamp": 1708272000000
    },
    {
      "version": "2",
      "stage": "Staging",
      "run_id": "def456",
      "creation_timestamp": 1708358400000
    }
  ]
}
```

#### 2.4 Transicionar Stage
```http
POST /api/v1/mlflow/models/climate-pricing-model/transition
Content-Type: application/json

{
  "version": "2",
  "stage": "Production"
}
```

**Resposta**:
```json
{
  "model": "climate-pricing-model",
  "version": "2",
  "stage": "Production",
  "status": "transitioned"
}
```

### Como Usar no Código

```python
from lib.mlflow_registry import get_mlflow

# Obter instância singleton
registry = get_mlflow()

# Treinar e registrar modelo
with registry.start_run(
    run_name="climate-pricing-v2",
    tags={"team": "climate", "type": "regression"},
):
    # Treinar
    model = train_model(X_train, y_train)
    
    # Log e registro
    registry.log_model(
        model=model,
        model_name="climate_pricing",
        registered_model_name="climate-pricing",
        metrics={"rmse": 0.15, "r2": 0.92},
        params={"n_estimators": 100, "max_depth": 10},
    )

# Carregar modelo de produção
model = registry.get_model(
    model_name="climate-pricing",
    stage="Production",
)

# Monitorar drift
psi_metrics = registry.log_drift_metrics(
    model_name="climate-pricing",
    version="2",
    reference_data=X_train,
    current_data=X_production,
    feature_columns=["temperature", "precipitation"],
)
```

### Iniciar MLflow Server

```bash
# Docker
docker run -d --name mlflow -p 5000:5000 \
  -v $(pwd)/mlflow:/mlflow \
  ghcr.io/mlflow/mlflow:latest \
  mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:////mlflow/mlflow.db \
  --default-artifact-root file:///mlflow/artifacts

# Ou diretamente
mlflow server \
  --host 0.0.0.0 \
  --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root file:///tmp/mlflow
```

### Acessar UI do MLflow
```
http://localhost:5000
```

---

## 📝 3. TIPOS TYPESCRIPT (OpenAPI)

### Gerar Tipos Atualizados

```bash
cd client

# Gerar tipos a partir do OpenAPI schema
npm run api:types

# Ou manualmente
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.d.ts
```

### Como Usar no Frontend

```typescript
import { PolicyPricingRequest, PolicyPricingResponse } from '@/types/api';

// Função type-safe para pricing
async function calculatePricing(
  request: PolicyPricingRequest
): Promise<PolicyPricingResponse> {
  const response = await fetch('/api/v1/policy-pricing/calculate', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'X-Request-ID': getRequestId(),
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error('Failed to calculate pricing');
  }
  
  return response.json() as Promise<PolicyPricingResponse>;
}

// Uso com type-checking
const pricing = await calculatePricing({
  asset_value: 100000,
  severity_amount: 10000,
  frequency_pct: 10,
});

// Type-safe: autocomplete e validação em compile-time
console.log(pricing.financials.total_premium);
```

### Tipos Disponíveis

- `ClimaData` - Dados climáticos
- `PolicyPricingRequest/Response` - Pricing
- `CidadeInfo` - Localização
- `HealthCheckResponse` - Health check
- `AuthRequest/Response` - Autenticação
- `ParametricInsuranceRequest/Response` - Seguro paramétrico
- `ApiResponse<T>` - Wrapper genérico
- `PaginatedResponse<T>` - Paginação
- `ApiError` - Erros

---

## 🧪 Testar Endpoints

### Via curl

```bash
# Vault Status
curl http://localhost:8000/api/v1/vault/status

# MLflow Status
curl http://localhost:8000/api/v1/mlflow/status

# Listar modelos MLflow
curl http://localhost:8000/api/v1/mlflow/models

# OpenAPI Schema (para gerar tipos TypeScript)
curl http://localhost:8000/openapi.json
```

### Via Swagger UI
```
http://localhost:8000/docs
```

Buscar por:
- `vault` - Endpoints do Vault
- `mlflow` - Endpoints do MLflow

---

## 📊 Status no Health Check

Ao iniciar o servidor, o log mostrará:

```
INFO: ============================================================
INFO: STATUS DOS SERVIÇOS TIER 1:
INFO: ============================================================
INFO: ✓ Vault Secrets Manager: http://localhost:8200
INFO: ✓ MLflow Model Registry: http://localhost:5000
INFO: ============================================================
INFO: Servidor ClimateWise iniciado com sucesso
```

Se não configurados:
```
WARNING: ⚠ Vault Secrets Manager: Não configurado
WARNING: ⚠ MLflow Model Registry: Não configurado
```

---

## 📁 Arquivos Modificados

| Arquivo | Modificação |
|---------|-------------|
| `server/main.py` | +200 linhas (Vault + MLflow) |
| `server/requirements.txt` | hvac==2.3.0 |
| `server/requirements-ml.txt` | mlflow==2.19.0 |
| `client/src/types/api.d.ts` | Tipos TypeScript |

---

## ✅ Checklist de Validação

```
[✓] Vault endpoints criados (/api/v1/vault/*)
[✓] MLflow endpoints criados (/api/v1/mlflow/*)
[✓] Tipos TypeScript gerados
[✓] Health check atualizado
[✓] Logs de inicialização
[✓] Fallback quando não configurado
[✓] Imports validados
```

---

## 🚀 Próximos Passos

1. **Instalar dependências**:
   ```bash
   cd server
   pip install hvac==2.3.0 mlflow==2.19.0
   ```

2. **Iniciar serviços**:
   ```bash
   # Vault
   docker run -d --name vault -p 8200:8200 -e 'VAULT_DEV_ROOT_TOKEN_ID=my-token' hashicorp/vault:latest
   
   # MLflow
   docker run -d --name mlflow -p 5000:5000 ghcr.io/mlflow/mlflow:latest mlflow server --host 0.0.0.0 --port 5000
   ```

3. **Configurar .env**:
   ```bash
   VAULT_URL=http://localhost:8200
   VAULT_TOKEN=my-token
   MLFLOW_TRACKING_URI=http://localhost:5000
   ```

4. **Reiniciar servidor**:
   ```bash
   cd server
   uvicorn main:app --reload
   ```

5. **Testar endpoints**:
   ```bash
   curl http://localhost:8000/api/v1/vault/status
   curl http://localhost:8000/api/v1/mlflow/status
   ```

---

*Guia criado em: 18 de Fevereiro de 2026*
*Versão: 1.0*
