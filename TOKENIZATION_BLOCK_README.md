# 🌍 ClimateAI: Tokenização de Índices Climáticos & Blockchain

Este documento descreve a arquitetura, regras de negócio e integração técnica para a tokenização de ativos climáticos (RWA - Real World Assets) utilizando a infraestrutura do **Google Cloud Blockchain**.

---

## 🏛️ Panorama Geral
O ClimateAI transforma dados climáticos brutos em ativos digitais líquidos. Através da tokenização, eventos de risco (seca, inundação, geada) são convertidos em tokens ERC-20, permitindo a criação de seguros paramétricos automáticos e derivativos financeiros transparentes.

### Benefícios:
- **Liquidação Instantânea**: Payouts automáticos via Smart Contracts.
- **Transparência**: Dados de oráculos (Open-Meteo/NOAA) auditáveis on-chain.
- **Eficiência**: Redução drástica de custos operacionais e de auditoria manual.

---

## 🛠️ Arquitetura de Implementação

O fluxo de processamento é dividido em quatro camadas principais:

1.  **Ingestão de Dados**: Captura de dados históricos e em tempo real via APIs meteorológicas.
2.  **Motor Atuarial (Python)**: Processamento e cálculo de índices climáticos personalizados.
3.  **Serviço de Tokenização**: Geração de metadata e comunicação com a Blockchain.
4.  **Google Blockchain Node Engine**: Infraestrutura escalável para interação com a rede distribuída.

---

## ⚖️ Regras de Negócio e Lógica de Índices

### 1. Critérios de Elegibilidade
Apenas eventos que ultrapassam limiares de impacto são tokenizados:
- **Score de Severidade (1-5)**: Calculado com base em Intensidade (40%), Probabilidade (30%), Duração (20%) e Extensão Geográfica (10%).
- **Threshold**: Somente eventos com Score ≥ 3 são convertidos em Tokens.

### 2. Algoritmos de Índices Climáticos
- **Rainfall Index**: Monitoramento de precipitação acumulada em janelas de 3 a 5 dias para detecção de inundações.
- **Drought Index**: Comparação da umidade de solo e chuva vs. mediana histórica de 20 anos.
- **Geração de Hash**: Cada token possui um ID imutável gerado por: `TIPO_EVENTO-NIVEL-HASH_LOC-HASH_TEMP-TIMESTAMP`.

---

## ☁️ Integração com Google Cloud Blockchain

O ClimateAI utiliza o **Google Cloud Blockchain Node Engine (BNE)** para garantir estabilidade empresarial:

### Configuração da Rede (RPC)
A plataforma conecta-se a um nó dedicado no BNE, garantindo maior taxa de transferência e menor latência comparado a provedores compartilhados.

### Gestão de Chaves e Segurança
- **Secret Manager**: Armazenamento seguro de chaves privadas e endereços de contratos inteligentes.
- **KMS Integration**: Assinatura de transações via HSM (Hardware Security Module) para conformidade e segurança institucional.

```python
# Exemplo de inicialização via Google Secret Manager (TokenizationService.py)
client = secretmanager.SecretManagerServiceClient()
secret_name = f"projects/{project_id}/secrets/BC_NODE_URL/versions/latest"
response = client.access_secret_version(name=secret_name)
node_url = response.payload.data.decode("UTF-8")
```

---

## 🚀 Como Criar e Emitir Tokens

1.  **Detectar o Evento**: O motor de risco identifica um alerta.
2.  **Gerar o Registro**: O `TokenizacaoEventosService` gera a estrutura `EventoToken`.
3.  **Mintagem On-Chain**:
    ```bash
    # O comando interno de mint disparado pelo serviço
    python server/scripts/deploy_tokenization.py
    ```
4.  **Validação**: O hash da transação (`tx_hash`) é vinculado ao laudo climático para auditoria perpétua.

---

## 📄 Smart Contracts
O contrato principal (`ClimateToken.sol`) implementa um padrão ERC-20 com permissões de administração via endereço do nó gerenciado no GCP, garantindo que apenas a plataforma possa emitir novos ativos baseados em dados reais.
