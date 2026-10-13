# ☁️ Akash Network - Inferência Descentralizada ClimateWise

Este diretório contém os manifestos de implantação **SDL (Stack Definition Language)** para rodar o serviço de inferência de IA do **ClimateWise** ([server/inference_server.py](file:///Users/leandrofrancademello/Projetos/ClimateWise/server/inference_server.py)) em GPUs descentralizadas da **Akash Network**.

---

## 🎯 Por que Akash Network?

1. **Redução de Custos de GPU**: Economia de 60% a 80% comparado a instâncias GPU no GCP/AWS (NVIDIA RTX 4090, A100, A6000).
2. **Arquitetura Desacoplada**: A API principal do ClimateWise consome a inferência via HTTP REST através da variável `INFERENCE_SERVICE_URL`.
3. **Resiliência e Fallback Local**: Se o lease ou nó da Akash oscilar, o serviço [`LSTMWithAttentionService`](file:///Users/leandrofrancademello/Projetos/ClimateWise/server/services/lstm_attention_service.py) executa automaticamente o cálculo na CPU local sem causar falhas aos usuários.

---

## 📁 Arquivos Disponíveis

* **`deploy-inference.yaml`**: Manifesto SDL para inferência acelerada por GPU (NVIDIA RTX 4090 / A100 / A6000 / L40S, 4 vCPUs, 16Gi RAM, 50Gi Storage).
* **`deploy-inference-cpu.yaml`**: Manifesto SDL econômico para execução apenas em CPU (2 vCPUs, 4Gi RAM).
* **`deploy.sh`**: Script auxiliar de validação e disparo da implantação.

---

## 🚀 Como Implantar

### Opção 1: Via Akash Console Web (Recomendado)

1. Acesse o painel [Akash Console](https://console.akash.network/).
2. Conecte sua carteira Web3 (Keplr, Leap ou MetaMask) ou faça login com sua conta/API Key.
3. Clique em **Deploy** -> **Upload SDL**.
4. Selecione o arquivo [`deploy-inference.yaml`](file:///Users/leandrofrancademello/Projetos/ClimateWise/deploy/akash/deploy-inference.yaml).
5. Escolha um dos provedores de GPU auditados que apresentarem lance (*bid*).
6. Confirme o lease.
7. Copie o hostname/URI do serviço provisionado (ex.: `https://xxxx.provider.akash.network:8001`).

### Opção 2: Via Akash CLI / API

1. Configure as variáveis em seu `.env`:
   ```bash
   AKASH_API_KEY="sua_chave_aqui"
   ```
2. Execute o deploy:
   ```bash
   ./deploy/akash/deploy.sh gpu
   ```

---

## 🔌 Conectando ao Backend ClimateWise

Após a subida do container na Akash Network, basta apontar a URL pública no arquivo `.env` do servidor:

```env
INFERENCE_SERVICE_URL="https://xxxx.provider.akash.network:8001"
```

O backend testará a conectividade via `/health` automaticamente e passará a direcionar o processamento pesado de redes neurais e do agente Poseidon para o cluster da Akash!
