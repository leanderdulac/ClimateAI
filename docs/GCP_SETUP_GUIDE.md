# ☁️ GCP Setup Guide: ClimateWise Production Environment

Este guia descreve os passos necessários para configurar a infraestrutura do Google Cloud para o ecossistema ClimateWise RWA.

## 1. Google Cloud KMS (HSM Signing)
Usado para assinar transações na blockchain sem expor chaves privadas.

1. **Habilitar API**: `gcloud services enable cloudkms.googleapis.com`
2. **Criar KeyRing**:
   ```bash
   gcloud kms keyrings create climate-keyring --location global
   ```
3. **Criar Chave Assimétrica (HSM)**:
   ```bash
   gcloud kms keys create eth-signing-key \
       --location global \
       --keyring climate-keyring \
       --purpose asymmetric-encryption \
       --protection-level hsm \
       --default-algorithm ec-sign-p256-sha256
   ```
4. **Permissões**: Garanta que o Service Account do backend tenha o papel `roles/cloudkms.signerVerifier`.

## 2. Google Earth Engine (Satellite Data)
Usado para capturar métricas de NDVI e umidade do solo.

1. **Atribuição de Conta**: Crie um Service Account e registre-o no [console do Earth Engine](https://code.earthengine.google.com/).
2. **Credenciais**: Salve o JSON da chave e configure a variável `GOOGLE_APPLICATION_CREDENTIALS`.

## 3. Blockchain Node Engine (BNE)
Usado como o node RPC de alta performance e baixa latência.

1. **Provisionamento**: No console do GCP, vá em "Blockchain Node Engine".
2. **Setup Polygon/Ethereum**: Escolha a rede (ex: Polygon Mainnet/Mumbai).
3. **Endpoint**: Copie a URL gerada e configure como `BC_NODE_URL`.

## 4. BigQuery (Transparency Audit)
Usado para armazenar os logs de auditoria cruzada (Chain + Satélite).

1. **Dataset**: Crie um dataset chamado `audit`.
2. **Tabela**: Crie uma tabela `payouts` com o schema:
   - `tx_hash` (STRING)
   - `ndvi_value` (FLOAT)
   - `severity_score` (FLOAT)
   - `timestamp` (TIMESTAMP)

## Variáveis de Ambiente Necessárias
```env
GOOGLE_CLOUD_PROJECT=seu-projeto-id
KMS_KEY_PATH=projects/seu-projeto/locations/global/keyRings/climate-keyring/cryptoKeys/eth-signing-key/cryptoKeyVersions/1
BC_NODE_URL=https://seu-bne-endpoint.com
GEE_SERVICE_ACCOUNT=seu-sa@seu-projeto.iam.gserviceaccount.com
```
