# Poseidon

Assistente local (Ollama) e centro de comando advisory da CEDAE. Não inventa chuva, vazão, turbidez nem telemetria SCADA. Ollama/Grok/Gemini **não** entram no caminho de escrita/controle; o chat é briefing.

## Modelo (chat)

Base: `qwen3.8:27b-mlx` (já no disco). Alias:

```bash
cd server/poseidon
ollama create poseidon -f Modelfile
ollama run poseidon
```

## API (JWT)

Chat (inalterado):

- `GET /api/v1/poseidon/status`
- `POST /api/v1/poseidon/chat` `{ "messages": [{ "role": "user", "content": "..." }] }`

CCO CEDAE (fixtures; `meta.live=false`):

- `GET /api/v1/poseidon/cco/systems` — ETAs/sistemas, concessionárias e parcelas fixture da produção Guandu
- `GET /api/v1/poseidon/cco/cma` — CMA Botafogo (09/06/2026, 36 câmeras / 14 pontos; **não** câmeras ao vivo)
- `GET /api/v1/poseidon/cco/connectors` — INEA, Alerta Rio, ANA HidroWeb, CEMADEN, INMET, CPTEC, ONS, El Niño; sonda ferramentas já existentes (Open-Meteo / ENSO / SAR / Alerta Rio) ou `status=stub` com URL de docs
- `GET /api/v1/poseidon/cco/psa` — Plano de Segurança da Água (estado em memória + limiares)
- `GET /api/v1/poseidon/cco/incidents` — linha do tempo in-memory
- `POST /api/v1/poseidon/cco/demo/geosmina` — simulação de bloom / laudo
- `POST /api/v1/poseidon/cco/demo/guandu-50` — cenário 50% (21/07/2026 18h)
- `GET /api/v1/poseidon/cco/demanda?horizonte_h=24` — previsão 1–48 h (clampeado)

Na plataforma: rota `/poseidon` (HMI do CCO; chat como briefing recolhível).

## Três modelos advisory

1. **geosmina** — entradas: proxy de ficocianina, temperatura, vazão baixa, laudo de geosmina e 2-MIB (µg/L). Regras: laudo ≥ 0,02 µg/L (bruta) **ou** (proxy alto + temp alta + vazão baixa) → `alerta`; laudo ≥ 0,1 **ou** proxy e laudo elevados → `critico`. Devolve PSA + SOP em português. **Nunca** afirma sensor online de geosmina em ng/L.
2. **guandu_outage** — fração de produção (default 0,5); 22 500 L/s restantes rateados pelas parcelas fixture (Águas do Rio 68% blocos 1+4, Iguá 17% bloco 2, Rio+ 15% bloco 3). Lista concessionárias/municípios em risco. Cita o evento 21/07/2026 18h como **cenário**, não como leitura ao vivo. Novo Guandu (mar/2030) é capacidade virtual.
3. **demanda** — 1–48 h de produção L/s por sistema a partir de curva diurna fixture + covariáveis de tempo (Open-Meteo via ferramentas existentes; se falhar, tempo fixture). Ponto + banda. Só advisory.

Envelope `{data, meta}` igual ao de `poseidon_tools` (`lib.partner_contract.envelope`). Telemetria CEDAE nestes endpoints é sempre fixture (`meta.live=false`).

Ferramenta `get_paraiba_reservoirs` lê a tabela pública do ANA SAR (`/sar0/MedicaoSin`) para Funil, Paraibuna, Jaguari e Santa Branca e calcula o equivalente da bacia. Sem linha na tabela → `unavailable`.
